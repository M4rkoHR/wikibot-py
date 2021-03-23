import discord
from discord.ext import commands, tasks
import settings
import asyncio
import requests

endpoint_url="https://top.gg/api"

class TopGG(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.token = settings.TopGGtoken # set this to your DBL token
    
    @tasks.loop(minutes=30.0)
    async def update_stats(self):
        header={"Authorization": self.token}
        print('Attempting to post server count')
        try:
            data={"server_count": int(len(self.bot.guilds))}
            requests.post("{endpoint}/bots/{bot_id}/stats".format(endpoint=endpoint_url, bot_id=str(self.bot.user.id)), data=data, headers=header)
            print('Posted server count ({})'.format(len(self.bot.guilds)))
        except Exception as e:
            print('Failed to post server count\n{}: {}'.format(type(e).__name__, e))


def setup(client):
    client.add_cog(TopGG(client))