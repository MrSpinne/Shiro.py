import discord
from discord.ext import commands
from library import checks

import psutil
import time


class Utility(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["searchsong"])
    async def search(self, ctx, title):
        """Search for a song in database"""
        songs = self.shiro.get_all_songs()


def setup(shiro):
    shiro.add_cog(Utility(shiro))
