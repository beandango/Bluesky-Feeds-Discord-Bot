import discord
from discord import app_commands
from discord.ext import commands, tasks
from datetime import datetime
import pytz
import re
import json
import requests

CONFIG_FILE = "config.json"
PUBLIC_API_BASE_URL = "https://public.api.bsky.app/xrpc"  # public bsky api endpoint

class Bsky(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_handle = None
        self.channel_id = None
        self.last_post_id = None
        
        # Load configuration on initialization
        self.load_config()
        
        # Start checking for new posts
        self.check_new_posts.start()

    def load_config(self):
        # Load the configuration to get channel ID and user handle
        config = self.load_config_json()
        self.channel_id = config.get("CHANNEL_ID")
        self.user_handle = config.get("BLSKY_USER_HANDLE")  # Store user handle for public access
    

    @staticmethod
    def load_config_json():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Config file not found. Creating a new one.")
            with open(CONFIG_FILE, "w") as f:
                json.dump({"CHANNEL_ID": None, "BLSKY_USER_HANDLE": None}, f)
            return {"CHANNEL_ID": None, "BLSKY_USER_HANDLE": None}

    @tasks.loop(minutes=5)
    async def check_new_posts(self):
        # Ensure the user handle and channel ID are set
        if not self.user_handle or not self.channel_id:
            print("User handle or channel ID not set. Please run the setup command.")
            return

        # Fetch and send the latest post if it’s new
        channel = self.bot.get_channel(self.channel_id)
        if channel:
            await self.send_latest_post(channel, force=False)

    async def send_latest_post(self, channel, force=False, interaction: discord.Interaction = None, msg: str = ""):
        """
        Fetches the latest post from the specified user and sends it to the given channel.
        If force is True, it bypasses the last_post_id check to always fetch and send the post.
        """
        try:
            # Make an unauthenticated request to get the author's feed
            url = f"{PUBLIC_API_BASE_URL}/app.bsky.feed.getAuthorFeed"
            params = {
                "actor": self.user_handle,
                "limit": 1,
                "filter": "posts_with_replies"
            }
            response = requests.get(url, params=params)

            # Check if the response is successful
            if response.status_code == 200:
                feed = response.json()
                if "feed" in feed and feed["feed"]:
                    latest_post = feed["feed"][0]
                    latest_post_id = latest_post["post"]["uri"]
                    handle = latest_post["post"]["author"]["handle"]
                    post_id = latest_post_id.split('/')[-1]
                    post_url = f"https://bsky.app/profile/{handle}/post/{post_id}"

                    # Default values for a regular post
                    msg = 'New Bluesky post!'
                    post_text = latest_post["post"]["record"].get("text", "")
                    created_at_str = latest_post["post"]["record"].get("createdAt", "")
                    display_name = latest_post["post"]["author"].get("displayName", handle)
                    profile_image = latest_post["post"]["author"].get("avatar")
                    color = discord.Color.green()
                    media_url = None  # Default media URL

                    # Check if the post is a repost
                    if "reason" in latest_post and latest_post["reason"].get("$type") == "app.bsky.feed.defs#reasonRepost":
                        msg = "Repost:"
                        color = discord.Color.blue()
                        original_post = latest_post["post"]
                        # Use the text and author details from the original post
                        post_text = original_post["record"].get("text", "")
                        display_name = original_post["author"].get("displayName", original_post["author"]["handle"])
                        profile_image = original_post["author"].get("avatar")
                        post_url = f"https://bsky.app/profile/{original_post['author']['handle']}/post/{original_post['uri'].split('/')[-1]}"

                    # Check if the post is a quote repost
                    elif "embed" in latest_post["post"]["record"] and latest_post["post"]["record"]["embed"].get("$type") == "app.bsky.embed.record#view":
                        msg = "Quote:"
                        color = discord.Color.orange()
                        quote_data = latest_post["post"]["record"]["embed"]["record"]
                        # Use quoted text and author details
                        post_text = quote_data["value"].get("text", "")
                        display_name = quote_data["author"].get("displayName", quote_data["author"]["handle"])
                        profile_image = quote_data["author"].get("avatar")
                        post_url = f"https://bsky.app/profile/{quote_data['author']['handle']}/post/{quote_data['uri'].split('/')[-1]}"

                    # Check if it's a reply
                    if "reply" in latest_post and "parent" in latest_post["reply"]:
                        reply_data = latest_post["reply"]["parent"]
                        replyparenthandle = reply_data["author"].get("handle", "unknown_handle")
                        replyparentlink = reply_data.get("uri", "").split('/')[-1]
                        msg = f'Replying to [{replyparenthandle}](https://bsky.app/profile/{replyparenthandle}/post/{replyparentlink}):'

                    # Check if this is a new post or if force is True
                    if self.last_post_id != latest_post_id or force:
                        self.last_post_id = latest_post_id

                        # Parse the created_at timestamp in UTC and convert to EST
                        created_at_est = datetime.now(pytz.timezone('America/New_York'))
                        if created_at_str:
                            created_at_utc = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
                            created_at_est = created_at_utc.astimezone(pytz.timezone('America/New_York'))

                        # Parse hashtags from the post text
                        hashtags = re.findall(r"#(\w+)", post_text)
                        for tag in hashtags:
                            hashtag_link = f"[#{tag}](https://bsky.app/hashtag/{tag})"
                            post_text = post_text.replace(f"#{tag}", hashtag_link)

                        if not display_name:
                            display_name = handle

                        # Extracting the image URL (thumbnail or fullsize) from post["embed"]["images"]
                        embed_content = latest_post["post"].get("embed", None)

                        if embed_content:
                            # Check if it's an image embed and retrieve fullsize URL if available, fallback to thumb
                            if embed_content.get("$type") == "app.bsky.embed.images#view":
                                media_url = embed_content["images"][0].get("fullsize") or embed_content["images"][0].get("thumb")

                        if not display_name:
                            display_name = handle

                        # Create the embed for the post
                        embed = discord.Embed(
                            description=post_text,
                            timestamp=created_at_est,
                            color=color,
                            title=display_name,
                            url=post_url
                        )
                        embed.set_thumbnail(url=profile_image)
                        if media_url:
                            embed.set_image(url=media_url)

                        # Add Post Link as a field
                        embed.add_field(name="Post Link", value=f"[View Post]({post_url})", inline=False)

                        # Send the message with the embed
                        if interaction:
                            await interaction.response.send_message(content=msg, embed=embed, ephemeral=True)
                        else:
                            await channel.send(content=msg, embed=embed)
                else:
                    print(f"Error fetching posts: HTTP {response.status_code} - {response.text}")
                        
        except Exception as e:
            print(f"Error fetching posts: {e}")


    # Slash command to re-fetch the latest post, forcing the send
    @app_commands.command(name="getpost", description="Fetch the latest post from Bluesky")
    async def getpost(self, interaction: discord.Interaction, hidden: bool = True):
        msg = ""
        if not interaction.user.guild_permissions.administrator and not hidden:
            hidden = True
            msg = "### Only admins can send this message without being hidden!\n"

        channel = interaction.channel
        await self.send_latest_post(channel, force=True, interaction=interaction, msg=msg)
        if not hidden:
            await interaction.response.send_message("Fetched the latest post!", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Bsky(bot))
