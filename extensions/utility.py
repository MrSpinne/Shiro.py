import discord
from discord.ext import commands
from library import checks, converters

import difflib
import asyncio


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
    async def edittitle(self, ctx, id: converters.SongID, title: converters.LengthStr(35)):
        """Edit song title in database"""
        await self.update_song(ctx, id, "Title", title)

    @commands.command(aliases=["changereference", "ereference", "eref"])
    @commands.check(checks.is_team)
    async def editreference(self, ctx, id: converters.SongID, reference: converters.Anime):
        """Edit song reference in database"""
        await self.update_song(ctx, id, "Reference", reference)

    @commands.command(aliases=["changeurl", "eurl"])
    @commands.check(checks.is_team)
    async def editurl(self, ctx, id: converters.SongID, url: converters.YoutubeURL):
        """Edit song url in database"""
        await self.update_song(ctx, id, "URL", url)

    @commands.command(aliases=["changecategory", "ecategory", "ecat"])
    @commands.check(checks.is_team)
    async def editcategory(self, ctx, id: converters.SongID, category: converters.Category):
        """Edit song url in database"""
        await self.update_song(ctx, id, "category", category)

    async def update_song(self, ctx, id, setting, value):
        """Update song in database and send before/after"""
        before = self.shiro.get_song(id)
        self.shiro.edit_song(id, setting.lower(), value)
        after = self.shiro.get_song(id)

        embed = discord.Embed(color=7830745, title=_("**\\🔧 {0} changed**").format(setting),
                              description=_("You've updated the song with the id `{0}`.").format(id))
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
                              description=_("Bot will stop in 5 minutes, {0} players will be shut down.").format(
                                  len(self.shiro.lavalink.players)))
        message = await ctx.send(embed=embed)

        embed = discord.Embed(color=10892179, title=_("\\❌ **Bot update**"),
                              description=_("We have detected that you're currently running playback. We're sorry, but"
                                            "we have to stop it after this song because we're rolling out a new "
                                            "update. This will occur in 5 minutes, please be patient."))

        songs_cog = self.shiro.get_cog("Songs")
        for player in self.shiro.lavalink.players:
            player_ctx = player.fetch("ctx")
            songs_cog.stop_playback(player_ctx)
            await player_ctx.send(embed=embed)

        for command in self.shiro.walk_commands():
            command.update(enabled=False)

        await asyncio.sleep(300)
        await message.delete()
        embed = discord.Embed(color=7830745, title=_("**\\🔧 Bot update**"),
                              description=_("Bot will now be shut down. {0}").format(ctx.author.mention))
        await ctx.send(embed=embed)


def setup(shiro):
    shiro.add_cog(Utility(shiro))
