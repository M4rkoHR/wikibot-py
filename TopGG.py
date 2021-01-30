import dbl
import settings
from discord.ext import commands


class TopGG(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.token = settings.TopGGtoken
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True) # Autopost will post your guild count every 30 minutes

    async def on_guild_post(self):
        print("Server count posted successfully")

def setup(client):
    client.add_cog(TopGG(client))