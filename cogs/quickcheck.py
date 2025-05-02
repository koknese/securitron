import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import app_commands, Embed, ui
from datetime import datetime, UTC
from misc.paginator import Pagination
import sqlite3
import requests
import json
from discord.app_commands import Group, command
from discord.ext.commands import GroupCog

load_dotenv('../.version', override=True)
load_dotenv('../.config', override=True)
server_id = int(os.getenv('SERVER_ID'))
version = os.getenv('VERSION')
confirmationChannel = int(os.getenv('CONFIRMATION_CHANNEL'))
ID_API_ENDPOINT = "https://users.roblox.com/v1/usernames/users"
PRESENCE_API_ENDPOINT = "https://presence.roblox.com/v1/presence/users"

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

def yieldResults(table, roblox_username):
    conn = sqlite3.connect('data.sqlite')
    c = conn.cursor()
    c.execute(f"SELECT * FROM {table} WHERE roblox_username = ?", (roblox_username.lower(),))
    row = c.fetchone()
    if row:
        return True
    else:
        return False
    c.close()
    conn.close()

def getHeadshot(roblox_username):
    userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(roblox_username)}&format=png&size=352x352"
    response = requests.get(userRawHeadshot)
    if response.status_code == 200:
        userParsedHeadshot = response.json()
        userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
        return userFinalHeadshot
    else:
        placeholderImg = "https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fi.imgflip.com%2Fd0tb7.jpg&f=1&nofb=1&ipt=e1c23bf6c418254a56c19b09cc9ece6238ead393652e54278f0d535f9fb81c56"
        return placeholderImg

def determineOnlineStatus(status):
    if status == 0:
        return "OFFLINE"
    elif status == 1:
        return "WEBSITE"
    elif status == 2:
        return "IN-GAME"

        
class Quickcheck(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @app_commands.command(
        name="quickcheck",
        description="Quickly check someone"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def quickcheck(self, interaction:discord.Interaction, roblox_username: str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return
        try:
            await interaction.response.defer(thinking=True)
            embed = discord.Embed(colour=0xf66151)
            embed.set_author(name="Securitas Quickcheck")
            embed.add_field(name="Has ID",
                            value=yieldResults("ids", roblox_username),
                            inline=False)
            embed.add_field(name="Is in Raiderwatch",
                            value=yieldResults("raiders", roblox_username),
                            inline=False)
            
            embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
            embed.set_thumbnail(url=getHeadshot(roblox_username))
            await interaction.followup.send(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.followup.send(embed=embed)
        except IndexError:
                embed = discord.Embed(title="User does not exist on Roblox!", colour=0xc01c28, description="Perhaps they've been banned?")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.followup.send(embed=embed)
        except Exception as e: 
            embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
            embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
            await interaction.followup.send(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Quickcheck(bot), guild=discord.Object(id=server_id))
