import os
import asyncio
import discord
from discord.ext import commands
import sys
import ctypes
from config import load_config
from typing import Optional, Literal

ctypes.windll.kernel32.SetConsoleTitleW("Bluesky Posts")

config = load_config()
TOKEN = config["TOKEN"]

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


@bot.command()
@commands.guild_only()
@commands.is_owner()
async def sync(ctx: commands.Context, guilds: commands.Greedy[discord.Object], spec: Optional[Literal["~", "*", "^"]] = None) -> None:
    if not guilds:
        if spec == "~":
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "*":
            ctx.bot.tree.copy_global_to(guild=ctx.guild)
            synced = await ctx.bot.tree.sync(guild=ctx.guild)
        elif spec == "^":
            ctx.bot.tree.clear_commands(guild=ctx.guild)
            await ctx.bot.tree.sync(guild=ctx.guild)
            synced = []
        else:
            synced = await ctx.bot.tree.sync()

        await ctx.send(
            f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
        )
        return

    ret = 0
    for guild in guilds:
        try:
            await ctx.bot.tree.sync(guild=guild)
        except discord.HTTPException:
            pass
        else:
            ret += 1

    await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


async def main():
    async with bot:
        await load()
        await bot.start(TOKEN)

asyncio.run(main())
