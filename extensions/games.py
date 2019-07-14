import discord
from discord.ext import commands
from library import checks, converters

import asyncio
import json
import random
import youtube_dl
import requests


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get("title")
        self.url = data.get("url")

    @classmethod
    async def from_url(cls, url, *, loop=None):
        ytdl_format_options = {
            "format": "bestaudio/best",
            "outtmpl": "cache/%(extractor)s-%(id)s-%(title)s.%(ext)s",
            "restrictfilenames": True,
            "noplaylist": True,
            "nocheckcertificate": True,
            "ignoreerrors": False,
            "logtostderr": False,
            "quiet": True,
            "no_warnings": True,
            "default_search": "auto",
            "source_address": "0.0.0.0"
        }
        ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=True))
        filename = ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, options="-vn"), data=data)


class Games(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro
        self.entries = {}

    @commands.command(aliases=["animequiz", "guesssong"])
    @commands.check(checks.voice_available)
    async def songquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Starts playing anime songs"""
        points = {}
        await ctx.author.voice.channel.connect()
        member_mentions = " ".join([member.mention for member in ctx.voice_client.channel.members if not member.bot])
        embed = discord.Embed(color=7830745, title=_("**\👾 Song quiz ‧ Starting**"),
                              description=_("Get ready, the quiz will start in 3 seconds!\n{0}").format(member_mentions))
        message = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await message.delete()

        for i in range(0, rounds):
            song, songs = await self.get_songs()
            self.shiro.loop.create_task(self.fade_song(ctx, song["youtube_url"]))
            message = await self.send_round_embed(ctx, i, rounds, songs)
            await asyncio.sleep(30)
            self.shiro.loop.create_task(self.fade_song(ctx))

            round_winner = await self.get_round_winner(song, songs, message.id)
            if round_winner is not None:
                if round_winner.id not in points:
                    points[round_winner.id] = 1
                else:
                    points[round_winner.id] += 1

            self.entries.pop(message.id, None)
            await message.delete()
            round_winner = round_winner.mention if round_winner is not None else _("Nobody")
            embed.title = _("**\👾 Song quiz ‧ Round {0}/{1}**").format(i + 1, rounds)
            embed.description = _("{0} has won the round!\nSong: [{1} ‧ {2}]({3})") \
                .format(round_winner, song["anime"], song["title"], song["youtube_url"])
            message = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await message.delete()

        max_points = max(points.values()) if len(points.values()) != 0 else []
        winner_ids = [user_id for user_id, user_points in points.items() if user_points == max_points]
        winners = [self.shiro.get_user(winner_id) for winner_id in winner_ids]

        embed = discord.Embed(color=7830745, title=_("**\👾 Song quiz ‧ End**"))

        if len(winners) == 0:
            embed.description = _("Nobody won the song quiz! There were {0} rounds.").format(rounds)
        elif len(winners) == 1:
            embed.description = _("{0} has guessed {1}/{2} songs correctly and won!") \
                .format(winners[0].mention, points[winner_ids[0]], rounds)
        else:
            embed.description = _("{0} have scored a draw with {1}/{2} songs correctly guessed each.") \
                .format(", ".join([user.mention for user in winners]), points[winner_ids[0]], rounds)

        await ctx.send(embed=embed)
        await ctx.voice_client.disconnect()

    async def send_round_embed(self, ctx, i, rounds, songs):
        """Send the default round embed and add reactions"""
        embed = discord.Embed(color=7830745, title=_("**\👾 Song quiz ‧ Round {0}/{1}**").format(i + 1, rounds),
                              description=f"1️⃣ {songs[0]['anime']} ‧ {songs[0]['title']}\n"
                              f"2️⃣ {songs[1]['anime']} ‧ {songs[1]['title']}\n"
                              f"3️⃣ {songs[2]['anime']} ‧ {songs[2]['title']}\n"
                              f"4️⃣ {songs[3]['anime']} ‧ {songs[3]['title']}\n"
                              f"5️⃣ {songs[4]['anime']} ‧ {songs[4]['title']}")
        message = await ctx.send(embed=embed)
        self.entries[message.id] = {}
        await message.add_reaction("1⃣")
        await message.add_reaction("2⃣")
        await message.add_reaction("3⃣")
        await message.add_reaction("4⃣")
        await message.add_reaction("5⃣")
        return message

    async def get_songs(self):
        """Get 5 random songs from database"""
        while True:
            selection = self.shiro.get_random_songs()
            choice = selection[random.randint(0, 4)]
            if await self.validate_song(choice):
                return choice, selection

    async def fade_song(self, ctx, youtube_url=None):
        """Fade song in or out"""
        if youtube_url is not None:
            player = await YTDLSource.from_url(youtube_url, loop=self.shiro.loop)
            ctx.voice_client.play(player, after=lambda e: print("Player error: %s" % e) if e else None)

            for i in range(0, 26):
                ctx.voice_client.source.volume = i / 30
                await asyncio.sleep(0.1)
        else:
            for i in range(25, -1, -1):
                ctx.voice_client.source.volume = i / 30
                await asyncio.sleep(0.1)

            try:
                await ctx.voice_client.stop()
            except:
                pass

    async def validate_song(self, song):
        """Check if youtube video exists"""
        try:
            requests.get(f"https://www.youtube.com/oembed?format=json&url={song['youtube_url']}").json()
            return True
        except:
            self.shiro.sentry.capture_message(
                f"Song {song['title']} ({song['anime']}) with url \"{song['youtube_url']} isn't available anymore.")
            return False

    async def get_round_winner(self, song, songs, message_id):
        """Get the winner who first reacted with the correct song number"""
        if songs.index(song) == 0:
            correct_reaction = "1⃣"
        elif songs.index(song) == 1:
            correct_reaction = "2⃣"
        elif songs.index(song) == 2:
            correct_reaction = "3⃣"
        elif songs.index(song) == 3:
            correct_reaction = "4⃣"
        else:
            correct_reaction = "5⃣"

        for user_id, reaction in self.entries[message_id].items():
            if reaction == correct_reaction:
                return self.shiro.get_user(user_id)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Add user entry if he is in the voice channel"""
        if reaction.message.id in self.entries and not user.bot:
            if user.id not in self.entries[reaction.message.id]:
                self.entries[reaction.message.id][user.id] = reaction.emoji


def setup(shiro):
    shiro.add_cog(Games(shiro))
