import discord
from discord.ext import commands
from library import checks, converters

import difflib


class Utility(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["song", "lookup"])
    @commands.check(checks.is_team)
    async def search(self, ctx, *, query):
        """Search for a song in database"""
        songs = self.shiro.get_all_songs()
        strings = [f"[{song['reference']} ‧ {song['title']}]({song['url']}) | {song['id']} ‧ {song['category']}" for song in songs]
        results = difflib.get_close_matches(query, strings, cutoff=0)

        embed = discord.Embed(color=7830745, title=_("**\\🔧 Song search**"),
                              description=_("Top results for `{0}`").format(query, "\n".join(results)))

        for result in results:
            split = result.rsplit(" | ")
            embed.add_field(name=split[1], value=split[0], inline=False)

        await ctx.send(embed=embed)

    @commands.command(aliases=["changetitle", "etitle", "etit"])
    @commands.check(checks.is_team)
    async def edittitle(self, ctx, song_id: converters.SongID, *, title: converters.LengthStr(35)):
        """Edit song title in database"""
        await self.update_song(ctx, song_id, "Title", title)

    @commands.command(aliases=["changereference", "ereference", "eref"])
    @commands.check(checks.is_team)
    async def editreference(self, ctx, song_id: converters.SongID, *, reference):
        """Edit song reference in database"""
        await self.update_song(ctx, song_id, "Reference", reference)

    @commands.command(aliases=["changeurl", "eurl"])
    @commands.check(checks.is_team)
    async def editurl(self, ctx, song_id: converters.SongID, *, url: converters.YoutubeURL):
        """Edit song url in database"""
        await self.update_song(ctx, song_id, "URL", url)

    @commands.command(aliases=["changecategory", "ecategory", "ecat"])
    @commands.check(checks.is_team)
    async def editcategory(self, ctx, song_id: converters.SongID, *, category: converters.Category):
        """Edit song url in database"""
        await self.update_song(ctx, song_id, "category", category)

    async def update_song(self, ctx, song_id, setting, value):
        """Update song in database and send before/after"""
        before = self.shiro.get_song(song_id)
        self.shiro.edit_song(song_id, setting.lower(), value)
        after = self.shiro.get_song(song_id)

        embed = discord.Embed(color=7830745, title=_("**\\🔧 {0} changed**").format(setting),
                              description=_("You've updated the song with the id `{0}`.").format(song_id))
        embed.add_field(name=_("{0} ‧ {1} (Before)").format(before["id"], before["category"]),
                        value=f"[{before['reference']} ‧ {before['title']}]({before['url']})", inline=False)
        embed.add_field(name=_("{0} ‧ {1} (After)").format(after["id"], after["category"]),
                        value=f"[{after['reference']} ‧ {after['title']}]({after['url']})")
        await ctx.send(embed=embed)

    @commands.command(aliases=["shutdown", "update"])
    @commands.check(checks.is_owner)
    async def commit(self, ctx):
        """Shut down bot for update"""
        embed = discord.Embed(color=7830745, title=_("**\\🔧 Bot update**"),
                              description=_("Bot stopping, {0} audio players will be shut down.").format(
                                  len(self.shiro.lavalink.players)))
        await ctx.send(embed=embed)
        self.shiro.shutdown()

def setup(shiro):
    shiro.add_cog(Utility(shiro))
