import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import app_commands, Embed, ui
from datetime import datetime
import time
import sqlite3
import requests
import json
from discord.app_commands import Group, command
from discord.ext.commands import GroupCog

load_dotenv('../.version', override=True)
load_dotenv('../.config', override=True)
server_id = int(os.getenv('SERVER_ID'))
version = os.getenv('VERSION')
baseloadPollChannel = int(os.getenv('BASELOAD_POLL_CHANNEL'))
baseloadChannel = int(os.getenv('BASELOAD_CHANNEL'))
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"

role1 = 1339345543486509104
role2 = 1358963787407032321

def getUserId(username):
    requestPayload = {
            "usernames": [
                username
            ],
            "excludeBannedUsers": True # Whether to include banned users within the request, change this as you wish
           }
        
    responseData = requests.post(ID_API_ENDPOINT, json=requestPayload)
        
            # Make sure the request succeeded
    assert responseData.status_code == 200
        
    userId = responseData.json()["data"][0]["id"]
        
    print(f"getUserId :: Fetched user ID of username {username} -> {userId}")
    return userId

class Baseloading(GroupCog, group_name="baseload", group_description="Securitas baseloading system"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @command(
        name="poll",
        description="Start a baseload poll"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.describe(poll_end_time="Time in which the poll ends (in minutes)", reactions_required="How many reaction to the message are required for the poll to succeed")
    @app_commands.checks.has_permissions(manage_roles=True)
    async def poll(self, interaction: discord.Interaction, details: str, base: str, poll_end_time: int, reactions_required: str):
        unix_timestamp = int(time.time())
        timeInSec = poll_end_time * 60
        final_stamp = timeInSec + unix_timestamp
        print(timeInSec)
        print(unix_timestamp)
        embed = discord.Embed(colour=0x1c71d8)

        embed.set_author(name=f"{interaction.user} wants to host a baseload!",
                         icon_url=interaction.user.avatar.url)
        
        embed.add_field(name="Details:",
                        value=details,
                        inline=False)
        embed.add_field(name="Base used:",
                        value=base,
                        inline=False)
        embed.add_field(name="Reactions required:",
                        value=reactions_required,
                        inline=False)
        embed.add_field(name="Poll ends:",
                        value=f"<t:{final_stamp}:R>",
                        inline=False)

        channel = interaction.client.get_channel(baseloadPollChannel)
        message = await channel.send("@here", embed=embed)
        await message.add_reaction("✅")
        await interaction.response.send_message("Done!", ephemeral=True)

    @command(
        name="start",
        description="Start a baseload"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.checks.has_permissions(manage_guild=True)
    async def start(self, interaction: discord.Interaction):
        conn = sqlite3.connect('data.sqlite')
        c = conn.cursor()
        c.execute("SELECT * FROM ids WHERE discord_id = ?", (interaction.user.id,))
        row = c.fetchone()
        embed = discord.Embed(colour=0x1c71d8)
        if row:
            roblox_username_db = row[0]

            userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(roblox_username_db)}&format=png&size=352x352"
            response = requests.get(userRawHeadshot)
            if response.status_code == 200:
                userParsedHeadshot = response.json()
                userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
            else:
                embed = discord.Embed(title="[Errno 4] Unknown error!", description=response.text, colour=0xa51d2d)
                embed.set_image(url=f'https://http.cat/{response.status_code}.jpg')
                embed.set_footer(text=f"Securitas Managment {version}")
                await interaction.response.send_message(embed=embed)

            embed = discord.Embed(title="Request perms here",
                      url="https://canary.discord.com/channels/1339345543448756234/1339345545449439254",
                      colour=0x00b0f4,
                      timestamp=datetime.now())

            embed.set_author(name=f"{interaction.user} is hosting a baseload!",
                             icon_url=interaction.user.avatar.url)
            
            embed.add_field(name="User link:",
                            value=f"https://roblox.com/users/{getUserId(roblox_username_db)}/profile",
                            inline=False)

            embed.set_thumbnail(url=userFinalHeadshot)
            channel = interaction.client.get_channel(baseloadChannel)

            await channel.send("@here", embed=embed)
            await interaction.response.send_message("Done!", ephemeral=True)
        else:
            await interaction.response.send_message("Your data is not registered in data.sqlite. Do you have an ID registered?", ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(Baseloading(bot), guild=discord.Object(id=server_id))
