import os
import asyncio
from dotenv import load_dotenv
import discord
from discord.ext import commands
import sys
import ctypes

ctypes.windll.kernel32.SetConsoleTitleW("Bluesky Posts")


load_dotenv()

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), intents=discord.Intents.all())

# Determine the base directory path (useful for PyInstaller executables)
if getattr(sys, 'frozen', False):
    # Running in a bundle
    base_dir = sys._MEIPASS
else:
    # Running in a normal Python environment
    base_dir = os.path.abspath(".")

async def load():
    # Use base_dir to correctly reference the `cogs` directory in both regular and PyInstaller environments
    cogs_dir = os.path.join(base_dir, 'cogs')
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            await bot.load_extension(f'cogs.{filename[:-3]}')

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} ({bot.user.id})")
    await bot.change_presence(activity=discord.Game(name="with rats"))

async def main():
    async with bot:
        await load()
        await bot.start(os.getenv('TOKENDANGO'))

asyncio.run(main())
