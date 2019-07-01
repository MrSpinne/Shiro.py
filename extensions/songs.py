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


class Songs(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro
        self.entries = {}

    @commands.command(brief="Songquiz starten", usage="[Runden]")
    @checks.voice_available()
    @commands.guild_only()
    async def songquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Starts playing anime songs"""
        points = {}
        i = 0
        await ctx.author.voice.channel.connect()

        embed = discord.Embed(color=7830745, title=f"**Songquiz ‧ Startet**",
                              description="Macht euch bereit, in wenigen Sekunden startet das Songquiz!")
        message = await ctx.send(embed=embed)
        await asyncio.sleep(3)
        await message.delete()

        while i < rounds:
            songs = self.get_songs()
            song = songs[random.randint(0, 4)]

            if not await self.validate_song(song):
                continue

            self.shiro.loop.create_task(self.fade_song(ctx, song["url"]))

            embed = discord.Embed(color=7830745, title=f"**Songquiz ‧ Runde {i + 1}/{rounds}**",
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
            embed.description = f"Die Runde hat {round_winner.mention if round_winner is not None else 'niemand'} " \
                                f"gewonnen!\nSong: [{song['anime']} ‧ {song['title']}]({song['url']})"
            message = await ctx.send(embed=embed)
            await asyncio.sleep(5)
            await message.delete()
            i += 1

        max_points = max(points.values()) if len(points.values()) != 0 else []
        winner_ids = [user_id for user_id, user_points in points.items() if user_points == max_points]
        winners = [self.shiro.get_user(winner_id) for winner_id in winner_ids]

        embed = discord.Embed(color=7830745, title=f"**Songquiz ‧ Ende**")

        if len(winners) == 0:
            embed.description = f"Niemand hat das Songquiz gewonnen! Es gab {rounds} Runde{'n' if rounds > 1 else ''}."
        elif len(winners) == 1:
            embed.description = f"{winners[0].mention} hat {points[winner_ids[0]]}/{rounds} Song" \
                                f"{'s' if rounds > 1 else ''} richtig erraten und somit gewonnen!"
        else:
            embed.description = f"{', '.join([user.mention for user in winners])} haben mit jeweils " \
                                f"{points[winner_ids[0]]}/{rounds} richtig erratenen Song" \
                                f"{'s' if rounds > 1 else ''} ein Unentschieden erzielt."

        await ctx.send(embed=embed)
        await ctx.voice_client.disconnect()

    def get_songs(self, amount=5):
        """Get 5 random songs from file"""
        with open("data/songs.json", "r", encoding="utf8") as file:
            songs = json.load(file)
            selection = random.sample(songs, k=amount)
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

    async def validate_song(self, song):
        """Check if youtube video exists"""
        try:
            requests.get(f"https://www.youtube.com/oembed?format=json&url={song['url']}").json()
            return True
        except:
            embed = discord.Embed(color=10892179, title="**Fehler bei Songquiz**",
                                  description=f"Der Song {song['anime']} ‧ {song['title']} mit der URL "
                                  f"[{song['url']}]({song['url']}) ist nicht mehr verfügbar.")
            await self.shiro.app_info.owner.send(embed=embed)
            return False

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Add user entry if he is in the voice channel"""
        if reaction.message.id in self.entries and not user.bot:
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

    @commands.command()
    @commands.guild_only()
    @commands.is_owner()
    async def shuffle(self, ctx, songs: converters.RangeInt(1, 25) = 10):
        await ctx.author.voice.channel.connect()

        songs = self.get_songs(songs)
        embed = discord.Embed(color=7830745, title="**Zufällige Wiedergabe**",
                              description=f"Folgende Songs werden nun abgespielt:\n")
        for song in songs:
            embed.description += f"- {song['anime']} ‧ {song['title']}\n"

        await ctx.send(embed=embed)

        for song in songs:
            await self.fade_song(ctx, song["url"])
            while ctx.voice_client.is_playing():
                await asyncio.sleep(0.1)

        await ctx.voice_client.disconnect()


def setup(shiro):
    shiro.add_cog(Songs(shiro))
