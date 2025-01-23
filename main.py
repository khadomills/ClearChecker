from typing import Final
import os
import requests
import discord
from dotenv import load_dotenv
from discord import app_commands
from discord.ext import commands

# load tokens and secrets from .env
load_dotenv()
TOKEN: Final[str] = os.getenv('DISCORD_TOKEN')
ff_cid = os.getenv('FFLOGS_CID')
ff_csecret = os.getenv('FFLOGS_CSECRET')


# Get access token for bot session
def get_token(ff_cid: str, ff_csecret: str) -> str:
    url = "https://www.fflogs.com/oauth/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": ff_cid,
        "client_secret": ff_csecret
    }
    response = requests.post(url, data=data)
    return response.json().get("access_token")


# Initial bot setup
bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())
fflogs_access = get_token(ff_cid, ff_csecret)


# Bot setup when connected
@bot.event
async def on_ready() -> None:
    print(f'{bot.user} is now running!')
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands(s)")
    except Exception as e:
        print(e)


# verify # of CoD clears and assign appropriate role(s)
@bot.tree.command(name="clears")
@app_commands.describe(world="The name of the home world your character is on")
async def clears(interaction: discord.Interaction, world: str):
    # discord object variables
    my_server = interaction.guild
    cleared = my_server.get_role(1326350552879206503)
    uncleared = my_server.get_role(1326378462998564894)

    char_name = interaction.user.display_name
    # GraphQL query to get character clear information for CoD
    query = f"""
    {{
      characterData {{
        character(name: "{char_name}", serverSlug: "{world}", serverRegion: "NA") {{
          name
          id
          zoneRankings(zoneID: 66)
        }}
      }}
    }}
    """

    # Send the request
    url = "https://www.fflogs.com/api/v2/client"
    headers = {"Authorization": f"Bearer {fflogs_access}"}
    response = requests.post(url, json={"query": query}, headers=headers)
    response = response.json()
    print(response)

    # Check for empty (no clears or invalid char) or error response
    print(response['data']['characterData']['character'])
    if response['data']['characterData']['character'] is None:
        await interaction.response.send_message(f"Hey {interaction.user.mention}! Your clears of The Cloud of Darkness "
                                                f"(Chaotic) couldn't be verified. If this is in error, please"
                                                f" visit #manual-verification", ephemeral=True)
        member = interaction.user
        await member.add_roles(uncleared)


    # Extract total kills from fflogs response and add appropriate roles
    else:
        total_kills = response['data']['characterData']['character']['zoneRankings']['rankings'][0]['totalKills']
        print(f"Total Kills: {total_kills}")

        if total_kills >= 5:
            await interaction.response.send_message(
                f"Hey {interaction.user.mention}! You have {total_kills} total kills of"
                f" The Cloud of Darkness (Chaotic). Roles updated!", ephemeral=True)
            member = interaction.user
            await member.add_roles(cleared)
        else:
            await interaction.response.send_message(
                f"Hey {interaction.user.mention}! You have {total_kills} total kills of"
                f" The Cloud of Darkness (Chaotic). Please verify again after obtaining 5 clears. Cloudlet role "
                f"assigned.",
                ephemeral=True)
            member = interaction.user
            await member.add_roles(uncleared)


# start bot
def main() -> None:
    bot.run(token=TOKEN)


if __name__ == '__main__':
    main()
