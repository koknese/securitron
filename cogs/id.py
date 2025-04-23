import discord
import os
from discord.ext import commands
from discord import app_commands
from dotenv import load_dotenv
from discord import app_commands, Embed, ui
from datetime import datetime
import sqlite3
import requests
import json
from discord.app_commands import Group, command
from discord.ext.commands import GroupCog
import uuid

load_dotenv('../.version', override=True)
load_dotenv('../.config', override=True)
server_id = int(os.getenv('SERVER_ID'))
version = os.getenv('VERSION')
confirmationChannel = int(os.getenv('CONFIRMATION_CHANNEL'))
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

class Identificationui(ui.Modal, title='You are signing up for a Securitas ID ©'):
   username = ui.TextInput(label='Roblox username', placeholder="Type your username here...", style=discord.TextStyle.short)
   async def on_submit(self, interaction: discord.Interaction):
       roblox_username = self.username.value
       applicant = interaction.user.id
       class Confirmapplication(discord.ui.View):
           def __init__(self, roblox_username, securitasID, discordid, *, timeout=43200):
               super().__init__(timeout=timeout)
               self.roblox_username = roblox_username.lower()
               self.discordid =  applicant
               self.securitas_id = str(securitasID)

           @discord.ui.button(label="Accept application",style=discord.ButtonStyle.green)
           async def accept_application(self, interaction:discord.Interaction, view: discord.ui.View):
               try:
                   conn = sqlite3.connect('data.sqlite')
                   c = conn.cursor()
        
                   c.execute("""CREATE TABLE IF NOT EXISTS ids(
                                    roblox_username string NOT NULL,
                                    discord_id TEXT NOT NULL,
                                    securitas_id NOT NULL
                                    )""")
                   c.execute("SELECT 1 FROM ids WHERE roblox_username = ? LIMIT 1;", (self.roblox_username,))
                   if c.fetchone():
                       embed = discord.Embed(title="User with the same Roblox username already is registered!", colour=0xc01c28)
                       embed.set_footer(text=f"Securitas Managment v.{version}")
                       await interaction.response.send_message(embed=embed)
                       c.close()
                       conn.close()
                       return
        
                   c.execute("""INSERT INTO ids (roblox_username, discord_id, securitas_id)
                                    VALUES (?, ?, ?);
                                 """, (self.roblox_username, self.discordid, self.securitas_id))
        
                   embed = discord.Embed(title=f"User registered to database by {interaction.user}!", colour=0x2ec27e)
                   embed.set_footer(text=f"Securitas Managment v.{version}")
                       
                   conn.commit()
                   c.close()
                   conn.close()

                   await interaction.response.send_message(embed=embed)
                   print(self.discordid)
                   applicant = interaction.client.get_user(self.discordid)
                   await applicant.send("Your ID application in Securitas was accepted!")
               except Exception as e:
                   embed = discord.Embed(title="[Errno 4] Unknown error!", description=str(e), colour=0xa51d2d)
                   await interaction.response.send_message(embed=embed)

       class Confirmpreview(discord.ui.View):
           def __init__(self, *, timeout=180):
               super().__init__(timeout=timeout)
               self.embed = embed
               self.confirmationChannel = confirmationChannel

           @discord.ui.button(label="Accept preview",style=discord.ButtonStyle.green)
           async def accept_preview(self, interaction:discord.Interaction, view: discord.ui.View):
               await interaction.response.send_message("Preview accepted. Your ID was sent to the moderation team for further approval.", ephemeral=True)
               confirmationChannelParsed = interaction.client.get_channel(self.confirmationChannel)
               await confirmationChannelParsed.send("You have received an ID application!", embed=embed, view=Confirmapplication(roblox_username, securitasID, applicant))

       userRawHeadshot = f"https://thumbnails.roblox.com/v1/users/avatar-headshot?userIds={getUserId(self.username.value)}&format=png&size=352x352"
       response = requests.get(userRawHeadshot)

       if response.status_code == 200:
           userParsedHeadshot = response.json()
           userFinalHeadshot = userParsedHeadshot['data'][0]['imageUrl']
       else:
           embed = discord.Embed(title="[Errno 4] Unknown error!", description=response.text, colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{response.status_code}.jpg')
           embed.set_footer(text=f"Securitas Managment {version}")
           await interaction.response.send_message(embed=embed)

       securitasID = uuid.uuid5(uuid.NAMESPACE_DNS, self.username.value)
       embed = discord.Embed(colour=0xf66151,
                      timestamp=datetime.now())

       embed.set_author(name="SECURITAS DIGITAL ID (PREVIEW MODE)")

       embed.add_field(name="Roblox Username",
                       value=self.username.value,
                       inline=False)
       embed.add_field(name="Discord ID",
                       value=f"{interaction.user.id} | <@{interaction.user.id}>",
                       inline=False)
       embed.add_field(name="Securitas ID",
                       value=securitasID,
                       inline=False)
       
       
       embed.set_footer(text=f"Securitas Managment v.{version}")
       embed.set_thumbnail(url=userFinalHeadshot)

       await interaction.response.send_message(embed=embed, ephemeral=True, view=Confirmpreview())
   async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
       if interaction.response.is_done():
           embed = discord.Embed(title="[Errno 4] Unknown error!", description="God give us strength.", colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{error.status}.jpg')
           embed.set_footer(text=f"Ragecord Utils {version}")
           await interaction.send_message(embed=embed)
       else:
           embed = discord.Embed(title="[Errno 4] Unknown error!", description="God give us strength.", colour=0xa51d2d)
           embed.set_image(url=f'https://http.cat/{error.status}.jpg')
           embed.set_footer(text=f"Ragecord Utils {version}")
           await interaction.response.send_message(error, embed=embed)
        
class Identification(GroupCog, group_name="id", group_description="Securitas digital ID system"):
    def __init__(self, bot):
        self.bot = bot
        self._last_member = None

    @command(
        name="create",
        description="Create your Securitas ID"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def post(self, interaction:discord.Interaction):
        modal = Identificationui()
        await interaction.response.send_modal(modal)

    @command(
            name="view_from_roblox_username",
            description="Find an ID using a Roblox username"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    @app_commands.checks.has_any_role(role1, role2)
    async def find_by_roblox(self, interaction:discord.Interaction, roblox_username:str):
        try:
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE roblox_username = ?", (roblox_username.lower(),))
            row = c.fetchone()
            if row:
                roblox_username_db = row[0]
                discord_id_db = row[1]
                securitas_id_db = row[2]
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
                embed = discord.Embed(colour=0xf66151)
                embed.set_author(name="SECURITAS DIGITAL ID")

                embed.add_field(name="Roblox Username",
                                value=roblox_username_db,
                                inline=False)
                embed.add_field(name="Discord ID",
                                value=f"{discord_id_db} | <@{discord_id_db}>",
                                inline=False)
                embed.add_field(name="Securitas ID",
                                value=securitas_id_db,
                                inline=False)
                
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                embed.set_thumbnail(url=userFinalHeadshot)
                await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)

    @command(
            name="delete",
            description="Delete an ID using a Roblox username"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def delete(self, interaction:discord.Interaction, roblox_username:str):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)
            return

        try:
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE roblox_username = ?", (roblox_username.lower(),))
            row = c.fetchone()
            if row:
                c.execute("DELETE FROM ids WHERE roblox_username = ?", (roblox_username.lower(),))
                conn.commit()
                c.close()
                conn.close()
                embed = discord.Embed(title="ID deleted!",
                          description=f"ID {roblox_username} was deleted succesfully!",
                          colour=0x57e389,
                          timestamp=datetime.now())
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
        except discord.errors.MissingPermissions:
            await interaction.response.send_message("You are lacking permissions!", ephemeral=True)

    @command(
            name="view_from_discord_account",
            description="Find an ID using a Discord username"
    )
    @app_commands.checks.has_any_role(role1, role2)
    @app_commands.guilds(discord.Object(id=server_id))
    async def find_by_discord(self, interaction:discord.Interaction, user: discord.Member):
        try:
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE discord_id = ?", (user.id,))
            row = c.fetchone()
            if row:
                roblox_username_db = row[0]
                discord_id_db = row[1]
                securitas_id_db = row[2]
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
                embed = discord.Embed(colour=0xf66151)
                embed.set_author(name="SECURITAS DIGITAL ID")

                embed.add_field(name="Roblox Username",
                                value=roblox_username_db,
                                inline=False)
                embed.add_field(name="Discord ID",
                                value=f"{discord_id_db} | <@{discord_id_db}>",
                                inline=False)
                embed.add_field(name="Securitas ID",
                                value=securitas_id_db,
                                inline=False)
                
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                embed.set_thumbnail(url=userFinalHeadshot)
                await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)

    @command(
            name="view_own",
            description="View your own id"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def view_own(self, interaction:discord.Interaction):
        try:
            conn = sqlite3.connect('data.sqlite')
            c = conn.cursor()
            c.execute("SELECT * FROM ids WHERE discord_id = ?", (interaction.user.id,))
            row = c.fetchone()
            if row:
                roblox_username_db = row[0]
                discord_id_db = row[1]
                securitas_id_db = row[2]
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
                embed = discord.Embed(colour=0xf66151)
                embed.set_author(name="SECURITAS DIGITAL ID")

                embed.add_field(name="Roblox Username",
                                value=roblox_username_db,
                                inline=False)
                embed.add_field(name="Discord ID",
                                value=f"{discord_id_db} | <@{discord_id_db}>",
                                inline=False)
                embed.add_field(name="Securitas ID",
                                value=securitas_id_db,
                                inline=False)
                
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                embed.set_thumbnail(url=userFinalHeadshot)
                await interaction.response.send_message(":mag::white_check_mark: ID found!", embed=embed, ephemeral=True)
            else:
                embed = discord.Embed(title="ID not found!", colour=0xc01c28)
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)
        except sqlite3.OperationalError:
                embed = discord.Embed(title="SQL: Table not found!", colour=0xc01c28, description="Perhaps a database hasn't been generated yet? Creating an ID creates one!")
                embed.set_footer(text=f"Securitas Managment v.{version}", icon_url="https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fb.thumbs.redditmedia.com%2FOkTdkj9krJasoRW41aR-fEaPx9ptf0I1jq9k80b154A.png&f=1&nofb=1&ipt=61f1bf9a0a87897a8374c0762298f934685e0f2d70ff64ac51190c0eb92b5d6e")
                await interaction.response.send_message(embed=embed)

    @command(
            name="help",
            description="Get help with ID commands"
    )
    @app_commands.guilds(discord.Object(id=server_id))
    async def help(self, interaction:discord.Interaction):
        embed = discord.Embed(colour=0xf66151, title="Help")
        embed.set_author(name="SECURITAS DIGITAL ID")
        embed.add_field(name="/id create",
                        value="Start the process for creating your own ID. Once filled out, wait for approval.",
                        inline=False)
        embed.add_field(name="/id view_own",
                        value="View your own ID.",
                        inline=False)
        embed.add_field(name="/id view_from_roblox_username",
                        value="(Usage of this command is restricted) View someone's id from their Roblox username.",
                        inline=False)
        embed.add_field(name="/id view_from_discord_account",
                        value="(Usage of this command is restricted) View someone's id from their Discord account.",
                        inline=False)
        embed.add_field(name="/id delete",
                        value="(Usage of this command is restricted) Delete someone's id.",
                        inline=False)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Identification(bot), guild=discord.Object(id=server_id))
