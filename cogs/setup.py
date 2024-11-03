import discord
from discord import app_commands
from discord.ext import commands
import os
import json
from cryptography.fernet import Fernet
import re

CONFIG_FILE = "config.json"

class Setup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.key = self.get_or_create_encryption_key()
        self.cipher = Fernet(self.key)

    def get_or_create_encryption_key(self):
        key = os.getenv("ENCRYPTION_KEY")
        if not key:
            key = Fernet.generate_key()
            with open(".env", "a") as env_file:
                env_file.write(f"\nENCRYPTION_KEY={key.decode()}")
            print("Generated and saved new encryption key to .env")
        return key.encode()

    def load_config_json(self):
        try:
            with open(CONFIG_FILE, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            print("Config file not found. Creating a new one.")
            with open(CONFIG_FILE, "w") as f:
                json.dump({"CHANNEL_ID": None, "BLSKY_USER": None, "BLSKY_PASS": None}, f)
            return {"CHANNEL_ID": None, "BLSKY_USER": None, "BLSKY_PASS": None}

    def save_config_json(self, config):
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)

    async def login_to_bluesky(self, user, password):
        encrypted_user = self.cipher.encrypt(user.encode()).decode()
        encrypted_pass = self.cipher.encrypt(password.encode()).decode()
        
        config = self.load_config_json()
        config["BLSKY_USER"] = encrypted_user
        config["BLSKY_PASS"] = encrypted_pass
        self.save_config_json(config)

        # Trigger a re-login with the new credentials
        bsky_cog = self.bot.get_cog("Bsky")
        if bsky_cog:
            bsky_cog.load_config()  # Reload config in the Bsky cog to pick up new credentials
            await bsky_cog.login_to_bluesky()  # Ensure we attempt login with new credentials

    @app_commands.command(name="setup", description="Set up the bot configuration (admin only)")
    @app_commands.guild_only()
    async def setup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("You must be an administrator to use this command.", ephemeral=True)
            return
        
        await interaction.response.send_message("Starting setup process. Check your DMs.", ephemeral=True)
        dm_channel = await interaction.user.create_dm()

        # Step 1: Ask for the channel ID
        await dm_channel.send("Please enter the channel ID where you'd like to post Bluesky updates.")
        
        def check_channel(m):
            return m.author == interaction.user and m.channel == dm_channel

        try:
            channel_msg = await self.bot.wait_for("message", check=check_channel, timeout=60)
            channel_input = channel_msg.content.strip()

            match = re.match(r"<#(\d+)>", channel_input)
            if match:
                channel_id = int(match.group(1))
            else:
                channel_id = int(channel_input)

            if not self.bot.get_channel(channel_id):
                await dm_channel.send("Invalid channel ID. Please make sure the bot has access to this channel.")
                return

            # Update channel ID in config.json
            config = self.load_config_json()
            config["CHANNEL_ID"] = channel_id
            self.save_config_json(config)

            # Reload the config in Bsky cog
            bsky_cog = self.bot.get_cog("Bsky")
            if bsky_cog:
                bsky_cog.load_config()  # Reload config in the Bsky cog to pick up new channel ID
                await dm_channel.send(f"Channel set to: <#{channel_id}> and reloaded.")
            else:
                await dm_channel.send("Failed to reload Bsky cog configuration.")
        except Exception as e:
            await dm_channel.send("Failed to get the channel. Please restart the setup command.")
            print(f"Error during setup (channel selection): {e}")
            return

        # Step 2: Ask if the user wants to update the Bluesky account
        await dm_channel.send("Do you want to update the Bluesky account credentials? Reply with 'yes' or 'no'.")
        
        def check_yes_no(m):
            return m.author == interaction.user and m.channel == dm_channel and m.content.lower() in ["yes", "no"]

        try:
            response_msg = await self.bot.wait_for("message", check=check_yes_no, timeout=30)
            if response_msg.content.lower() == "no":
                await dm_channel.send("Setup complete. The Bluesky credentials were not updated.")
                return
            elif response_msg.content.lower() == "yes":
                # Proceed to ask for the Bluesky username and password
                await dm_channel.send("Please enter your Bluesky username (no one else can see this).")
                
                def check_user(m):
                    return m.author == interaction.user and m.channel == dm_channel

                user_msg = await self.bot.wait_for("message", check=check_user, timeout=60)
                username = user_msg.content

                await dm_channel.send("Please enter your Bluesky password (no one else can see this).")
                password_msg = await self.bot.wait_for("message", check=check_user, timeout=60)
                password = password_msg.content

                # Encrypt, store credentials, and re-login
                await self.login_to_bluesky(username, password)

                # Reload the config to ensure updated credentials are active in Bsky cog
                bsky_cog = self.bot.get_cog("Bsky")
                if bsky_cog:
                    bsky_cog.load_config()
                    await bsky_cog.login_to_bluesky()  # Re-login with updated credentials

                await dm_channel.send("Bluesky login credentials have been set. Configuration complete. You should delete the messages containing your credentials.")
        except Exception as e:
            await dm_channel.send("Setup failed. Please try again.")
            print(f"Error during setup (credentials): {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))
