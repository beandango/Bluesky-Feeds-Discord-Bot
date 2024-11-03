import discord
from discord import app_commands
import os
import json
from discord.ext import commands, tasks
import atproto
from datetime import datetime
import pytz
import re
from cryptography.fernet import Fernet
from dotenv import load_dotenv

load_dotenv()

CONFIG_FILE = "config.json"

class Bsky(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bsky_client = None
        self.bsky_profile = None  # Store the logged-in profile here
        self.user_id = None
        self.channel_id = None
        self.bsky_user = None  # Store encrypted user as a string
        self.bsky_pass = None  # Store encrypted pass as a string
        self.last_post_id = None
        
        # Load configuration on initialization
        self.load_config()
        
        # Start checking for new posts
        self.check_new_posts.start()

    def load_config(self):
        # Load encryption key from .env
        self.key = os.getenv("ENCRYPTION_KEY")
        if self.key:
            self.cipher = Fernet(self.key.encode())
        else:
            print("Encryption key not found. Please run the setup command to configure the bot.")
            return  # Exit the method without raising an error

        # Load dynamic configuration from config.json
        config = self.load_config_json()
        
        self.bsky_user = config.get("BLSKY_USER")
        self.bsky_pass = config.get("BLSKY_PASS")
        
        if self.bsky_user and self.bsky_pass:
            # Attempt to log in to Bluesky
            self.bot.loop.create_task(self.login_to_bluesky())
        else:
            print("Bluesky credentials not found. Please run the setup command.")
        
        # Load channel ID from config.json
        self.channel_id = config.get("CHANNEL_ID")
        if self.channel_id:
            self.bot.channel_id = int(self.channel_id)
        else:
            print("Channel ID not set. Please run the setup command.")

    @staticmethod
    def load_config_json():
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Config file not found. Creating a new one.")
            with open(CONFIG_FILE, "w") as f:
                json.dump({"CHANNEL_ID": None, "BLSKY_USER": None, "BLSKY_PASS": None}, f)
            return {"CHANNEL_ID": None, "BLSKY_USER": None, "BLSKY_PASS": None}

    @staticmethod
    def save_config_json(config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    def decrypt_credentials(self):
        # Decrypt the username and password
        user = self.cipher.decrypt(self.bsky_user.encode()).decode()
        password = self.cipher.decrypt(self.bsky_pass.encode()).decode()
        return user, password
    
    async def login_to_bluesky(self):
        # Ensure credentials are available before trying to log in
        if not self.bsky_user or not self.bsky_pass:
            print("Credentials not available. Please run the setup command.")
            return
        try:
            user, password = self.decrypt_credentials()
            self.bsky_client = atproto.Client()
            self.bsky_profile = self.bsky_client.login(user, password)  # Store profile in a separate attribute
            self.user_id = self.bsky_profile.did  # Set the user ID on successful login
            print("Successfully logged in to Bluesky.")
        except Exception as e:
            print(f"Failed to log in to Bluesky: {e}")

    @tasks.loop(minutes=1)
    async def check_new_posts(self):
        # Check if login is completed
        if not self.bsky_client or not self.user_id:
            await self.login_to_bluesky()  # Retry login if not already done
            if not self.user_id:  # If login still fails, skip this iteration
                print("Bluesky login required. Please run the setup command.")
                return

        # Proceed to check and send the latest post if channel ID is configured
        if self.bot.channel_id:
            channel = self.bot.get_channel(self.bot.channel_id)
            await self.send_latest_post(channel, hidden=False)

    # Helper function to send the latest post, with an optional `force` parameter
    async def send_latest_post(self, channel, hidden, interaction: discord.Interaction = None, msg=None, force=False):
        try:
            # Fetch the user's latest posts
            feed = self.bsky_client.get_author_feed(self.user_id, limit=1)
            
            if feed and feed.feed:
                latest_post = feed.feed[0]
                latest_post_id = latest_post.post.uri
                handle = latest_post.post.author.handle
                post_id = latest_post_id.split('/')[-1]
                post_url = f"https://bsky.app/profile/{handle}/post/{post_id}"

                # Check if this is a new post or if forced
                if self.last_post_id != latest_post_id or force:
                    self.last_post_id = latest_post_id
                    
                    # Extract basic post details
                    post_text = getattr(latest_post.post.record, 'text', '')

                    # Parse hashtags from the post text
                    hashtags = re.findall(r"#(\w+)", post_text)  # Extract words starting with #

                    # Replace each hashtag with a clickable link
                    for tag in hashtags:
                        hashtag_link = f"[#{tag}](https://bsky.app/hashtag/{tag})"
                        post_text = post_text.replace(f"#{tag}", hashtag_link)

                    created_at_str = latest_post.post.record.created_at
                    
                    # Parse the created_at timestamp in UTC and convert to EST
                    created_at_utc = datetime.strptime(created_at_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=pytz.UTC)
                    created_at_est = created_at_utc.astimezone(pytz.timezone('America/New_York'))
                    
                    # Retrieve profile details
                    profile = self.bsky_client.get_profile(self.user_id)
                    display_name = profile.display_name
                    profile_image = profile.avatar if hasattr(profile, 'avatar') else None
                    
                    # Initialize media placeholder
                    media_url = None
                    video_url = None
                    
                    # Check if embed_content exists
                    embed_content = getattr(latest_post.post.record, 'embed', None)
                    
                    if embed_content:
                        print("Embed content exists, proceeding to fetch detailed post thread.")
                        post_thread = self.bsky_client.get_post_thread(uri=latest_post_id, depth=0)
                        
                        # Access the first available image URL (fullsize)
                        if hasattr(post_thread.thread.post.embed, 'images'):
                            media_url = post_thread.thread.post.embed.images[0].fullsize

                        # Handle videos if present
                        elif hasattr(post_thread.thread.post.embed, 'playlist'):
                            video_url = post_thread.thread.post.embed.playlist
                            media_url = post_thread.thread.post.embed.thumbnail  # Use thumbnail for preview
                    
                    # Create the main embed with the post text, profile details, and media (if available)
                    main_embed = discord.Embed(
                        description=post_text,
                        timestamp=created_at_est,
                        color=discord.Color.green(),
                        title=display_name,
                        url=f'https://bsky.app/profile/{handle}'
                    )
                    
                    if video_url:
                        main_embed.add_field(name="Video Link", value=f"[Watch Video]({post_url})", inline=False)
                    else:
                        main_embed.add_field(name="Post Link", value=f"[View Post]({post_url})", inline=False)               

                    # Set the first image as the main embed's media
                    if media_url:
                        main_embed.set_image(url=media_url)
                    
                    main_embed.set_thumbnail(url=profile_image)

                    # Send the main embed
                    if channel and not hidden:
                        await channel.send(content=f'New Bluesky post!', embed=main_embed)
                    elif channel and hidden and interaction:
                        await interaction.response.send_message(content=f'{msg}New Bluesky post!', embed=main_embed, ephemeral=True)
                        
        except Exception as e:
            print(f"Error fetching posts: {e}")

    # Slash command to re-fetch the latest post, forcing the send
    @app_commands.command(name="getpost", description="Fetch the latest post from Bluesky")
    async def getpost(self, interaction: discord.Interaction, hidden: bool):
        eph = hidden
        msg = ''
        if not interaction.user.guild_permissions.administrator and not eph:
            eph = True
            msg = "### Only admins can send this message without being hidden!\n"
        channel = interaction.channel
        await self.send_latest_post(channel, eph, interaction, msg, force=True)  # Use force=True to bypass last_post_id check


async def setup(bot: commands.Bot):
    await bot.add_cog(Bsky(bot))
