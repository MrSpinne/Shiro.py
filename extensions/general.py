import discord
from discord.ext import commands
from library import checks, converters, exceptions

import time
import difflib
import re


class General(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["?", "cmd", "cmds", "command", "commands"])
    async def help(self, ctx):
        """Display all commands"""
        embed = discord.Embed(color=7830745, title=_("**\\📄 General**"))
        embed.description = _("`{0}help` ‧ Display all commands\n"
                              "`{0}info` ‧ Show credits of the bot and links (e.g. support server)\n"
                              "`{0}stats` ‧ List up some stats of Shiro\n"
                              "`{0}oprequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request opening for quiz\n"
                              "`{0}edrequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request ending for quiz\n"
                              "`{0}ostrequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request OST for quiz"
                              ).format(ctx.prefix)
        await ctx.author.send(embed=embed, content=_("Here're all commands for **{0}**:").format(ctx.guild.name))

        embed = discord.Embed(color=7830745, title=_("**\\🎵 Songs**"))
        embed.description = _("`{0}opquiz [1-25]` ‧ Guess anime openings with specified amount of rounds\n"
                              "`{0}edquiz [1-25]` ‧ Openings are too easy for you? This is next level!\n"
                              "`{0}ostquiz [1-25]` ‧ Guess OST's from animes! Only for pros.\n"
                              "`{0}stop` ‧ Stop running quiz or playback").format(ctx.prefix)
        await ctx.author.send(embed=embed)

        try:
            checks.is_guild_admin(ctx)
        except exceptions.NotGuildAdmin:
            return

        languages = "/".join(self.shiro.get_languages())
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Settings**"))
        embed.description = _("`{0}prefix <1-10 symbols>` ‧ Change server prefix\n"
                              "`{0}deletion <on/off>` ‧ Enable or disable command message deletion\n"
                              "`{0}channel <none/channel>` ‧ Set channel in which commands are allowed only\n"
                              "`{0}language <{1}>` ‧ Change bot language\n"
                              "`{0}config` ‧ Display current configuration").format(ctx.prefix, languages)
        await ctx.author.send(embed=embed)

        try:
            checks.is_team(ctx)
        except exceptions.NotTeam:
            return

        embed = discord.Embed(color=7830745, title=_("**\\🔧 Utility**"))
        embed.description = _("`{0}search <query>` ‧ Search for songs in database\n"
                              "`{0}edittitle <song id> <title>` ‧ Edit title of song\n"
                              "`{0}editreference <song id> <reference>` ‧ Edit reference of song\n"
                              "`{0}editurl <song id> <url>` ‧ Edit url of song\n"
                              "`{0}editcategory <song id> <category` ‧ Edit category of song").format(ctx.prefix)
        await ctx.author.send(embed=embed)

    @commands.command(aliases=["information", "about", "credits", "spinne", "shiro"])
    async def info(self, ctx):
        """Show credits of the bot"""
        owner = f"{self.shiro.app_info.owner.name}#{self.shiro.app_info.owner.discriminator}"
        embed = discord.Embed(color=7830745, title=_("**\\📄 About Shiro**"))
        embed.set_thumbnail(url=self.shiro.app_info.owner.avatar_url)
        embed.description = _("Shiro were made by **{0}** in Python. If you have any questions, feel free "
                              "to contact.\n\n[Support & Feedback]({1}) ‧ [Help translate]({1}) ‧ "
                              "[Vote]({2}) ‧ [All songs]({3})").format(
            owner, "https://discord.gg/5z4z8kh", "https://discordbots.org/bot/593116701281746955/vote",
            "https://docs.google.com/spreadsheets/d/1S8u-V3LBMSzf8g78ZEE1I7_YT8SSFa8ROpXysoqvSFg")
        await ctx.send(embed=embed)

    @commands.command(aliases=["status", "stat"])
    async def stats(self, ctx):
        """List up some stats of Shiro"""
        ping = time.monotonic()
        await self.shiro.application_info()
        ping = int((time.monotonic() - ping) * 1000)

        embed = discord.Embed(color=7830745, title=_("**\\📄 Statistics**"))
        embed.description = _("Guilds ‧ {0}\nUsers ‧ {1}\nAudio players ‧ {2}\nVotes (on dbl) ‧ {3}\nPing ‧ {4}ms\nSongs ‧ {5}").format(
            len(self.shiro.guilds), len(self.shiro.users), len(self.shiro.lavalink.players),
            len(await self.shiro.dbl.get_bot_upvotes()), ping, len(self.shiro.get_all_songs()))

        await ctx.send(embed=embed)

    @commands.command(aliases=["openingrequest", "openingreq", "opreq"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def oprequest(self, ctx, song: converters.LengthStr(35), anime: converters.Anime, yt_url: converters.YoutubeURL):
        """Request a song for the song quiz"""
        await self.do_request(ctx, song, anime, yt_url, "Opening")

    @commands.command(aliases=["endingrequest", "endingreq", "edreq"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def edrequest(self, ctx, song: converters.LengthStr(35), anime: converters.Anime, yt_url: converters.YoutubeURL):
        """Request a song for the ending quiz"""
        await self.do_request(ctx, song, anime, yt_url, "Ending")

    @commands.command(aliases=["ostreq"])
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ostrequest(self, ctx, song: converters.LengthStr(35), anime: converters.Anime, yt_url: converters.YoutubeURL):
        """Request a song for the ost quiz"""
        await self.do_request(ctx, song, anime, yt_url, "OST")

    async def do_request(self, ctx, title, reference, url, category):
        """Request a song for specified category"""
        embed = discord.Embed(color=7830745, title=_("**\\📄 {0} request**").format(category))
        embed.description = _("You requested [{0} ‧ {1}]({2}) to be added into the {3} quiz. "
                              "Thank you for your support, our bot staff will review it.").format(title, reference, url, category.lower())
        await ctx.send(embed=embed)

        song_string = f"[{reference} ‧ {title}]({url})"
        song_strings = [f"[{song['reference']} ‧ {song['title']}]({song['url']})" for song in self.shiro.get_all_songs()]
        added_songs = difflib.get_close_matches(song_string, song_strings, cutoff=0)
        added_songs = f"A. {added_songs[0]}\nB. {added_songs[1]}\nC. {added_songs[2]}"
        references = ctx.bot.anilist.search.anime(reference, perpage=3)
        print(references)
        references = [reference["title"] for reference in references["data"]["Page"]["media"]]
        references = [reference["english"] if reference.get("english") else reference["romaji"] for reference in references]
        recommended_songs = [f"[{title} ‧ {recommended_song}]({url})" for recommended_song in references]
        recommended_songs = f"1. {recommended_songs[0]}\n2. {recommended_songs[1]}\n3. {recommended_songs[2]}"

        embed = discord.Embed(color=7830745, title=f"**\\🔧 New {category} request**")
        embed.description = f"User **{ctx.author.name}#{ctx.author.discriminator}** requested {song_string}."
        embed.add_field(name="Already added", value=added_songs, inline=False)
        embed.add_field(name="Recommendations", value=recommended_songs)
        message = await self.shiro.get_channel(601374759724384272).send(embed=embed)
        await message.add_reaction("1⃣")
        await message.add_reaction("2⃣")
        await message.add_reaction("3⃣")
        await message.add_reaction("❌")
        # TODO: Add pending songs to database with specific status

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Add song to database if owner accepts"""
        emojis = ["1⃣", "2⃣", "3⃣", "❌"]
        channel = self.shiro.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        user = self.shiro.get_user(payload.user_id)

        try:
            if message.embeds[0].fields[1].name != "Recommendations" or message.author.bot:
                raise ValueError
            if payload.emoji.name not in emojis or payload.channel_id != 601374759724384272:
                raise ValueError
        except (AttributeError, IndexError, ValueError):
            return

        embed = message.embeds[0]
        value = embed.fields[1].value
        if payload.emoji.name == "❌":
            embed.set_footer(text=f"Declined by {user.name}#{user.discriminator}")
        else:
            lines = value.split("\n")
            category = re.search(r"\*\*\\\\🔧 New (.+?) request\*\*", embed.title)[0]
            songs = [re.search(r"\d. \[(.+?) ‧ (.+)\]\((.+)\)", line) for line in lines]
            index = emojis.index(payload.emoji.name)
            song = songs[index]
            embed.set_footer(text=f"Version {index+1} accepted by {user.name}#{user.discriminator}")
            self.shiro.add_song(song[1], song[0], song[2], category)

        await message.clear_reactions()
        await message.edit(embed=embed)


def setup(shiro):
    shiro.add_cog(General(shiro))
