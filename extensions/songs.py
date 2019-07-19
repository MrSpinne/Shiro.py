import discord
from discord.ext import commands
from library import checks, converters

import asyncio
import json
import random
import lavalink
import re
import collections


class Songs(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro
        self.entries = {}
        self.points = {}
        self.history = {}
        self.shiro.add_listener(self.shiro.lavalink.voice_update_handler, "on_socket_response")

    async def cog_before_invoke(self, ctx):
        """Connect to voice channel before playing audio"""
        player = self.shiro.lavalink.players.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        if checks.voice_available in ctx.command.checks and not player.is_connected:
            await self.connect_to(ctx.guild.id, ctx.author.voice.channel.id)
            self.entries[ctx.guild.id] = {}
            self.points[ctx.guild.id] = []
            self.history[ctx.guild.id] = {}

    async def connect_to(self, guild_id, channel_id):
        """Connects to voice channel, if None disconnects"""
        ws = self.shiro._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    async def cleanup_guild(self, guild_id):
        """Remove player of guild"""
        self.shiro.lavalink.players.remove(guild_id)
        del self.entries[guild_id]
        del self.points[guild_id]
        del self.history[guild_id]
        await self.connect_to(guild_id, None)

    def enqueue_tracks(self, ctx, tracks):
        """Enqueue all songs"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        for track in tracks:
            player.add(requester=ctx.author.id, track=track)

    async def get_random_tracks(self, ctx, category, amount):
        """Check songs got from database and return tracks"""
        tracks = []
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        songs = self.shiro.get_random_songs(category.lower(), amount)

        for song in songs:
            results = await player.node.get_tracks(song["url"])
            if not results or not results["tracks"]:
                self.shiro.sentry.capture_message(f"Invald Song URL: {song['url']}")
                continue

            track = results["tracks"][0]
            tracks.append(track)
            video_id = re.search("((?<=(v|V)/)|(?<=be/)|(?<=(\?|\&)v=)|(?<=embed/))([\w-]+)", song["url"])[0]
            self.history[ctx.guild.id][video_id] = song

        return tracks

    async def fade_volume(self, ctx, fade_in):
        """Fade volume in or out"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        loop_range = range(0, 81, 10) if fade_in else range(80, -1, -10)

        for i in loop_range:
            await player.set_volume(i)
            await asyncio.sleep(0.2)

    def get_current_round(self, ctx):
        """Get current round by looking up current track in history"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        return list(self.history[ctx.guild.id].keys()).index(player.current.identifier) + 1

    def get_song_choices(self, ctx, category):
        """Return songs to be chosen with one correct"""
        current_song = list(self.history[ctx.guild.id].values())[self.get_current_round(ctx) - 1]
        songs = self.shiro.get_choice_songs(category.lower(), current_song["url"])
        songs.append(current_song)
        random.shuffle(songs)
        return songs

    def get_round_winner(self, ctx, songs, message_id):
        """Get the winner who first reacted with the correct song number"""
        correct_song = list(self.history[ctx.guild.id].values())[self.get_current_round(ctx) - 1]
        index = songs.index(correct_song)
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣"]
        correct_reaction = reactions[index]

        for user_id, reaction in self.entries[ctx.guild.id][message_id].items():
            if reaction == correct_reaction:
                return self.shiro.get_user(user_id)

    async def run_round(self, ctx, category):
        """Start a round"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        song_choices = self.get_song_choices(ctx, category)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Round {1}/{2}**").format(
            category, self.get_current_round(ctx), len(self.history[ctx.guild.id])), description="")

        for index, song in enumerate(song_choices):
            embed.description += f"{emojis[index]} {song['reference']} ‧ {song['title']}\n"

        message = await ctx.send(embed=embed, delete_after=30.5)
        self.entries[ctx.guild.id][message.id] = {}
        await message.add_reaction("1⃣")
        await message.add_reaction("2⃣")
        await message.add_reaction("3⃣")
        await message.add_reaction("4⃣")
        await player.set_pause(False)
        await message.add_reaction("5⃣")

        await self.fade_volume(ctx, True)
        await asyncio.sleep(25)
        await self.fade_volume(ctx, False)

        winner = self.get_round_winner(ctx, song_choices, message.id)
        winner_mention = _("Nobody")
        if winner is not None:
            self.points[ctx.guild.id].append(winner.id)
            winner_mention = winner.mention

        song = list(self.history[ctx.guild.id].values())[self.get_current_round(ctx) - 1]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Round {1}/{2}**").format(
            category, self.get_current_round(ctx), len(self.history[ctx.guild.id])), description="")
        embed.description = _("{0} has won the round!\nSong: [{1} ‧ {2}]({3})").format(
            winner_mention, song["reference"], song["title"], song["url"])
        await ctx.send(embed=embed, delete_after=5)
        await asyncio.sleep(2.5)
        await player.set_pause(True)
        await asyncio.sleep(2.5)
        await player.skip()

    async def run_quiz(self, ctx, category, rounds):
        """Start a quiz with specified category"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        player.store("ctx", ctx)
        members = ctx.author.voice.channel.members
        member_mentions = " ".join([member.mention for member in members if not member.bot])
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Starting**").format(category),
                              description=_("Get ready, the quiz will start in 3 seconds!\n{0}").format(
                                  member_mentions))
        message = await ctx.send(embed=embed)

        await player.set_volume(0)
        tracks = await self.get_random_tracks(ctx, category.lower(), rounds)
        self.enqueue_tracks(ctx, tracks)
        await player.play()
        await player.set_pause(True)

        await asyncio.sleep(1)
        try:
            await message.delete()
        except:
            pass

        while player.queue or player.current:
            await self.run_round(ctx, category)

        counted = collections.Counter(self.points[ctx.guild.id])
        winners = [self.shiro.get_user(id) for id, points in dict(counted).items() if counted.most_common(1)[0][1] == points]
        winner_mentions = [winner.mention for winner in winners]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ End**").format(category))

        if len(winners) == 0:
            embed.description = _("Nobody won the song quiz! There were {0} round(s).").format(len(self.history[ctx.guild.id]))
        elif len(winners) == 1:
            embed.description = _("{0} has guessed {1}/{2} songs correctly and won!").format(
                winner_mentions[0], counted.most_common(1)[0][1], len(self.history[ctx.guild.id]))
        else:
            embed.description = _("{0} have scored a draw with {1}/{2} songs correctly guessed each.").format(
                " & ".join(winner_mentions), counted.most_common(1)[0][1], len(self.history[ctx.guild.id]))

        await ctx.send(embed=embed)
        await self.cleanup_guild(ctx.guild.id)

    @commands.command(aliases=["openings"])
    @commands.check(checks.voice_available)
    async def openingquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Guess anime openings with specified amount of rounds\n"""
        await self.run_quiz(ctx, "Opening", rounds)

    @commands.command(aliases=["endings"])
    @commands.check(checks.voice_available)
    @commands.check(checks.has_voted)
    async def endingquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Openings are too easy for you? This is next level!"""
        await self.run_quiz(ctx, "Ending", rounds)

    @commands.command(aliases=["end", "skip", "reduce"])
    @commands.check(checks.is_requester)
    @commands.check(checks.player_available)
    async def stop(self, ctx):
        """Stop running quiz or playback"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        played = len(self.history[ctx.guild.id]) - len(player.queue)
        guild_history_before = dict(self.history[ctx.guild.id])
        player.queue.clear()

        for i in range(0, played + 1):
            keys = list(self.history[ctx.guild.id].keys())
            del self.history[ctx.guild.id][keys[-1]]

        embed = discord.Embed(color=7830745, title=_("**\🎵 Stop quiz**"))
        if len(guild_history_before) == len(self.history[ctx.guild.id]):
            embed.description = _("Quiz already ends after this round. Playback will be stopped then.")
        else:
            embed.description = _("Reducing quiz rounds from {0} to {1}. Playback will end after current round.").format(
                len(guild_history_before), len(self.history[ctx.guild.id]))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Reconnect to voice channel if quiz is running"""
        player = self.shiro.lavalink.players.get(member.guild.id)
        if member.id == self.shiro.user.id and player is not None:
            if after.channel is None:
                ctx = player.fetch("ctx")
                prefix = self.shiro.get_guild_setting(ctx.guild.id, "prefix")
                await self.connect_to(member.guild.id, before.channel.id)
                embed = discord.Embed(color=10892179, title=_("\❌ **Bot kicked**"),
                                      description=_("The bot was kicked from voice channel so it reconnected. "
                                                    "You can stop the quiz with `{0}stop`").format(prefix))
                await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        """Add user entry if he is in the voice channel"""
        if reaction.message.guild is not None and not user.bot:
            if reaction.message.guild.id in self.entries:
                if reaction.message.id in self.entries[reaction.message.guild.id]:
                    if user.id not in self.entries[reaction.message.guild.id][reaction.message.id]:
                        self.entries[reaction.message.guild.id][reaction.message.id][user.id] = reaction.emoji


def setup(shiro):
    shiro.add_cog(Songs(shiro))
