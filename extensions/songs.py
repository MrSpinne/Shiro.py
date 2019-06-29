import discord
from discord.ext import commands
from library import checks

import asyncio
import json
import random
import youtube_dl


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
            "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
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


class Songs(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro
        self.entries = {}

    @commands.command()
    @commands.guild_only()
    @checks.voice_available()
    async def songquiz(self, ctx, rounds: int = 10):
        """Starts playing anime songs"""
        points = {"niemand": -1}
        await ctx.author.voice.channel.connect()

        embed = discord.Embed(color=7830745, title="Songquiz - Start", description="Startet...")
        message = await ctx.send(embed=embed)

        for i in range(0, rounds):
            songs = self.get_songs()
            song = songs[random.randint(0, 4)]

            try:
                self.shiro.loop.create_task(self.fade_song(ctx, song["url"]))
            except:
                continue

            embed.title = f"**Songquiz - Runde {i + 1}/{rounds}**"
            embed.description = f"1️⃣ {songs[0]['anime']} - {songs[0]['title']}\n" \
                                f"2️⃣ {songs[1]['anime']} - {songs[1]['title']}\n" \
                                f"3️⃣ {songs[2]['anime']} - {songs[2]['title']}\n" \
                                f"4️⃣ {songs[3]['anime']} - {songs[3]['title']}\n" \
                                f"5️⃣ {songs[4]['anime']} - {songs[4]['title']}"
            await message.edit(embed=embed)
            self.entries[message.id] = {}
            await message.add_reaction("1⃣")
            await message.add_reaction("2⃣")
            await message.add_reaction("3⃣")
            await message.add_reaction("4⃣")
            await message.add_reaction("5⃣")

            await asyncio.sleep(30)
            self.shiro.loop.create_task(self.fade_song(ctx))

            round_winner = await self.get_round_winner(song, songs, message.id)
            if round_winner is not None:
                if round_winner.id not in points:
                    points[round_winner.id] = 1
                else:
                    points[round_winner.id] += 1

            self.entries.pop(message.id, None)
            self.shiro.loop.create_task(message.clear_reactions())
            embed.description = f"Die Runde hat {round_winner.mention if round_winner is not None else 'niemand'} " \
                                f"gewonnen!\nSong: [{song['anime']} - {song['title']}]({song['url']})"
            await message.edit(embed=embed)
            await asyncio.sleep(5)

        winner_id = max(points, key=points.get)
        if winner_id != "niemand":
            description = f"Das Songquiz hat {self.shiro.get_user(winner_id).mention} " \
                          f"mit {points[winner_id]} richtigen Antworten gewonnen!"
        else:
            description = "Niemand hat das Songquiz gewonnen!"

        embed.title = f"**Songquiz - Ende**"
        embed.description = description
        await message.edit(embed=embed)

        await ctx.voice_client.disconnect()

    def get_songs(self):
        """Get 5 random songs from file"""
        with open("data/songs.json", "r") as file:
            songs = json.load(file)
            selection = random.sample(songs, k=5)
            return selection

    async def fade_song(self, ctx, url=None):
        """Fade song in or out"""
        if url is not None:
            async with ctx.typing():
                player = await YTDLSource.from_url(url, loop=self.shiro.loop)
                ctx.voice_client.play(player, after=lambda e: print("Player error: %s" % e) if e else None)

            for i in range(0, 26):
                ctx.voice_client.source.volume = i / 50
                await asyncio.sleep(0.1)
        else:
            for i in range(25, -1, -1):
                ctx.voice_client.source.volume = i / 50
                await asyncio.sleep(0.1)

            try:
                await ctx.voice_client.stop()
            except:
                pass

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Add user entry if he is in the voice channel"""
        if reaction.message.id in self.entries and not user.bot:
            await reaction.message.remove_reaction(reaction.emoji, user)
            if user.id not in self.entries[reaction.message.id]:
                self.entries[reaction.message.id][user.id] = reaction.emoji

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

        for key, value in self.entries[message_id].items():
            if value == correct_reaction:
                return self.shiro.get_user(key)


def setup(shiro):
    shiro.add_cog(Songs(shiro))
