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

def determineOnlineStatus(status):
    if status == 0:
        return "OFFLINE"
    elif status == 1:
        return "WEBSITE"
    elif status == 2:
        return "IN-GAME"

def getUserPresence(userId):
    payload = {
        "userIds": [userId]
    }
    headers = {
        "Content-Type": "application/json"
    }
    
    response = requests.post(PRESENCE_API_ENDPOINT, json=payload, headers=headers)
    
    last_location = response.json()['userPresences'][0]['lastLocation']
    presence_type = response.json()['userPresences'][0]['userPresenceType']
    print(presence_type)
    print(f"getUserPresence :: Fetched presence of {userId}")
    return last_location, presence_type
        
class Raiderwatch(GroupCog, group_name="raiderwatch", group_description="Securitas ID stalking system"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @command(
        name="register_raider",
        description="Add a raider to Raiderwatch Raider Registry"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def register(self, interaction:discord.Interaction, roblox_username: str, notes: str = None):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return

        conn = sqlite3.connect('data.sqlite')
        c = conn.cursor()
      
        c.execute("""CREATE TABLE IF NOT EXISTS raiders(
                                  roblox_username string NOT NULL,
                                  notes TEXT,
                                  first_registered TEXT NOT NULL,
                                  last_seen TEXT
                                  )""")
        c.execute("SELECT 1 FROM raiders WHERE roblox_username = ? LIMIT 1;", (roblox_username.lower(),))
        if c.fetchone():
            embed = discord.Embed(title="User with the same Roblox username already is registered!", colour=0xc01c28)
            embed.set_footer(text=f"Securitas Managment v.{version}")
            await interaction.response.send_message(embed=embed)
            c.close()
            conn.close()
            return
        
        utc_time = f"{datetime.now(UTC)} UTC"

        c.execute("""INSERT INTO raiders(roblox_username, notes, first_registered)
                 VALUES (?, ?, ?);
        """, (roblox_username.lower(), notes, utc_time))
      
        conn.commit()
        c.close()
        conn.close()

        embed = discord.Embed(title=f"User registered to Raiderwatch Registry by {interaction.user}!", colour=0x2ec27e)
        embed.set_footer(text=f"Securitas Managment v.{version}")
        await interaction.response.send_message(embed=embed)

    @command(
            name="check",
            description="Checks whether someone is a raider"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def raider_check(self, interaction:discord.Interaction, roblox_username:str):
        try:
            await interaction.response.defer(thinking=True)
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM raiders WHERE roblox_username = ?", (roblox_username.lower(),))
            row = c.fetchone()
            if row:
                roblox_username_db = row[0]
                notes_db = row[1]
                first_registered_db = row[2]
                last_seen_db = row[3]

                roblox_id = getUserId(roblox_username_db)
                last_location, presence_type = getUserPresence(roblox_id)

                userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(roblox_username_db)}&format=png&size=352x352"
                response = requests.get(userRawHeadshot)
                if response.status_code == 200:
                    userParsedHeadshot = response.json()
                    userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
                else:
                    embed = discord.Embed(title="[Errno 4] Unknown error!", description=response.text, colour=0xa51d2d)
                    embed.set_image(url=f'https://http.cat/{response.status_code}.jpg')
                    embed.set_footer(text=f"Securitas Managment {version}")
                    await interaction.followup.send(embed=embed)
                embed = discord.Embed(colour=0xf66151)
                embed.set_author(name="SECURITAS RAIDERWATCH")

                embed.add_field(name="Roblox Username",
                                value=roblox_username_db,
                                inline=False)
                embed.add_field(name="First registered",
                                value=first_registered_db,
                                inline=False)
                embed.add_field(name="Last seen",
                                value=last_seen_db,
                                inline=False)
                embed.add_field(name="Notes",
                                value=notes_db,
                                inline=False)
                embed.add_field(name="Last location in Roblox",
                                value=last_location,
                                inline=False)
                embed.add_field(name="Current status",
                                value=determineOnlineStatus(presence_type),
                                inline=False)

                
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                embed.set_thumbnail(url=userFinalHeadshot)
                await interaction.followup.send(":mag::white_check_mark: Raider found!", embed=embed)
            else:
                embed = discord.Embed(title="Raider not found!", colour=0xc01c28)
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.followup.send(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.followup.send(embed=embed)
        finally:
            c.close()
            conn.close()

    @command(
            name="delete",
            description="Delete an entry in Raiderwatch"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def delete(self, interaction:discord.Interaction, roblox_username:str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return

        try:
            await interaction.response.defer(thinking=True)
            with sqlite3.connect('data.sqlite') as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM raiders WHERE roblox_username = ?", (roblox_username.lower(),))
                row = c.fetchone()
                if row:
                    c.execute("DELETE FROM raiders WHERE roblox_username = ?", (roblox_username.lower(),))
                    conn.commit()
                    embed = discord.Embed(title="Entry deleted!",
                              description=f"Raiderwatch entry for {roblox_username} was deleted succesfully!",
                              colour=0x57e389,
                              timestamp=datetime.now())
                    embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                    await interaction.followup.send(embed=embed)
                else:
                    embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                    embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                    await interaction.followup.send(embed=embed)
        except sqlite3.OperationalError as e:
            embed = discord.Embed(title="SQL error!", colour=0xc01c28, description=f"Traceback:\n{e}")
            embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
            await interaction.followup.send(embed=embed)

    @command(
            name="update_last_seen",
            description="Update the last seen date for an entry in Raiderwatch"
    )
    async def update_last_seen(self, interaction:discord.Interaction, roblox_username:str):
        try:
            await interaction.response.defer(thinking=True)
            with sqlite3.connect('data.sqlite') as conn:
                c = conn.cursor()
                utc_time = f"{datetime.now(UTC)} UTC"
                c.execute("""
                UPDATE raiders
                SET last_seen = ?
                WHERE roblox_username = ?;
                """, (utc_time, roblox_username))

                conn.commit()
                
                embed = discord.Embed(title="Entry updated!",
                    description=f"Raiderwatch entry for {roblox_username} was updated succesfully!",
                    colour=0x57e389,
                    timestamp=datetime.now())
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.followup.send(embed=embed)
        except Exception as e:
            embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
            embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
            await interaction.followup.send(embed=embed)
        finally:
            c.close()
            conn.close()

     
    @command(name='list', description='List raiders')
    async def show(self, interaction: discord.Interaction):
        try:
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT roblox_username FROM raiders;")
            taglist = [row[0] for row in c.fetchall()]
            L = 10
            async def get_page(page: int):
                emb = discord.Embed(title="Raiderwatch raider list", description="")
                offset = (page-1) * L
                for tag in taglist[offset:offset+L]:
                    emb.description += f"`{tag}`\n"
                emb.set_author(name=f"Requested by {interaction.user}")
                n = Pagination.compute_total_pages(len(taglist), L)
                emb.set_footer(text=f"Page {page} from {n}")
                return emb, n
            await Pagination(interaction, get_page).navegate()
        except Exception as e:
            embed = discord.Embed(title="Unknown error occured!", colour=0xc01c28, description=f"```{e}```")
            embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
            await interaction.response.send_message(embed=embed)
               


    @command(
            name="help",
            description="Get help with Raiderwatch commands"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def help_raiderwatch(self, interaction:discord.Interaction):
        embed = discord.Embed(colour=0xf66151, title="Help")
        embed.set_author(name="SECURITAS RAIDERWATCH")
        embed.add_field(name="/raiderwatch register_raider",
                        value="(Usage of this command is restricted) Register a raid to the database",
                        inline=False)
        embed.add_field(name="/raiderwatch check",
                        value="Get info on a registered raider.",
                        inline=False)
        embed.add_field(name="/raiderwatch update_last_seen",
                        value="Update the last seen date for a raider.",
                        inline=False)
        embed.add_field(name="/raiderwatch list",
                        value="List all raiders.",
                        inline=False)
        embed.add_field(name="/raiderwatch delete",
                        value="(Usage of this command is restricted) Delete a raider from the database.",
                        inline=False)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Raiderwatch(bot), guild=discord.Object(id=server_id))
