import discord
from discord.ext import commands
from library import checks, converters

import psutil
import time
import difflib


class Utility(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["song", "lookup"])
    @commands.check(checks.is_team_member)
    async def search(self, ctx, *, query):
        """Search for a song in database"""
        songs = self.shiro.get_all_songs()
        strings = [f"[{song['reference']} ‧ {song['title']}]({song['url']}) | {song['id']} ‧ {song['category']}" for song in songs]
        results = difflib.get_close_matches(query, strings, cutoff=0)

        embed = discord.Embed(color=7830745, title=_("**\\🔧 Song search**"),
                              description=_("Top results for \"{0}\"").format(query, "\n".join(results)))

        for result in results:
            split = result.rsplit(" | ")
            embed.add_field(name=split[1], value=split[0], inline=False)

        await ctx.send(embed=embed)


def setup(shiro):
    shiro.add_cog(Utility(shiro))
