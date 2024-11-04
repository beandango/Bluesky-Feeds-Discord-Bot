import discord
from discord import app_commands
from discord.ext import commands
import re
from config import update_config_value  # Import functions from config.py

class Setup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

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
            update_config_value("CHANNEL_ID", channel_id)
            
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

        # Step 2: Ask for the Bluesky User Handle
        await dm_channel.send("Please enter the public Bluesky username (handle) of the account you'd like to monitor.")

        def check_handle(m):
            return m.author == interaction.user and m.channel == dm_channel

        try:
            handle_msg = await self.bot.wait_for("message", check=check_handle, timeout=60)
            user_handle = handle_msg.content.strip()

            # Update user handle in config.json
            update_config_value("BLSKY_USER_HANDLE", user_handle)

            # Reload the config in Bsky cog
            bsky_cog = self.bot.get_cog("Bsky")
            if bsky_cog:
                bsky_cog.load_config()  # Reload config in the Bsky cog to pick up new user handle
                await dm_channel.send(f"Bluesky user handle set to: {user_handle} and reloaded.")
            else:
                await dm_channel.send("Failed to reload Bsky cog configuration.")

            await dm_channel.send("Setup complete. The bot is now configured to monitor the specified Bluesky user handle.")

        except Exception as e:
            await dm_channel.send("Setup failed. Please try again.")
            print(f"Error during setup (Bluesky handle): {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Setup(bot))
