import discord
from discord.ext import commands
from discord import app_commands

class Help(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="help", description="setup help")
    async def help(self, interaction: discord.Interaction):
        embed = discord.Embed(
            color=discord.Color.dark_green(),
            title="Help",
            description="**/setup**\nUse this command to set up the bot configuration.The bot will DM you and guide you through the process.\n\n**Channel id**\nGo into your discord server, right click on the channel you want the posts to be automatically sent to, and click \"Copy Channel ID\". This is what you give the bot in DMs when it asks you for a channel id.\n*if you cannot see the option to copy channel id, see this link:* https://support.discord.com/hc/en-us/articles/206346498-Where-can-I-find-my-User-Server-Message-ID\n\n**/getpost**\nThis command forces the bot to grab the most recent post into whatever channel you used the `/setup` command. Made for debugging purposes. \nSet \"hidden\" to `True` to make the message only visible to you, otherwise, set it to `False` to make it visible to everyone.\n\n**/help**\nThis command shows this help menu.")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot:commands.Bot):
    await bot.add_cog(Help(bot))