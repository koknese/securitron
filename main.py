import discord
from discord import app_commands
from discord.utils import get, format_dt
from discord.ext import commands
from dotenv import load_dotenv
import os
from datetime import datetime
intents = discord.Intents.all()
intents.members = True

load_dotenv('./.config', override=True)
load_dotenv('.version', override=True)
server_id = os.getenv('SERVER_ID')
token = os.getenv('TOKEN')
version = os.getenv('VERSION')
bot = commands.Bot(command_prefix="sudo ", intents=intents)
tree = bot.tree

print(server_id)

@tree.command(name="load", description="DEBUG: load a cog", guild=discord.Object(id=server_id))
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def load_cog(interaction: discord.Interaction, extension: str):
    await bot.load_extension(f"cogs.{extension}")
    await interaction.response.send_message(f"Cog '{extension}' loaded.")
    await tree.sync(guild=discord.Object(id=server_id)) 
    print(f"Cog '{extension}' has been loaded.")
    
@tree.command(name="unload", description="DEBUG: unload a cog", guild=discord.Object(id=server_id))
@discord.app_commands.checks.has_permissions(manage_messages=True)
async def load_cog(interaction: discord.Interaction, extension: str):
    await bot.unload_extension(f"cogs.{extension}")
    await interaction.response.send_message(f"Cog '{extension}' unloaded.")
    await tree.sync(guild=discord.Object(id=server_id)) 
    print(f"Cog '{extension}' has been unloaded.")
    
@tree.command(name="force-sync", description="DEBUG: forcesync", guild=discord.Object(id=server_id))
@discord.app_commands.checks.has_permissions(administrator=True)
async def forcesync(interaction: discord.Interaction):
    await interaction.response.send_message("Force sync...")
    await tree.sync(guild=discord.Object(id=server_id)) 
    print(f"FORCE SYNC.")

@bot.event
async def on_ready():
    print(f"We have logged in as {bot.user}")
    
    await bot.load_extension("cogs.id")
    await tree.sync(guild=discord.Object(id=server_id))  # Sync the commands after loading the cog
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name =f"YouTube poops"))
    print(discord.__version__)

@bot.event
async def on_member_join(member):
    joinRole = discord.Object(id=default_role)
    await member.add_roles(joinRole)
    
bot.run(token)
