import discord
from discord.ext import commands
from library import checks, converters

import asyncio
import random
import collections
import lavalink


class Songs(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro
        self.shiro.add_listener(self.shiro.lavalink.voice_update_handler, "on_socket_response")
        self.shiro.lavalink.add_event_hook(self.on_lavalink_event)

    async def cog_before_invoke(self, ctx):
        """Connect to voice channel before playing audio"""
        player = self.shiro.lavalink.players.create(ctx.guild.id, endpoint=str(ctx.guild.region))
        if checks.voice_available in ctx.command.checks and not player.is_connected:
            await self.connect_to(ctx.guild.id, ctx.author.voice.channel.id)

    async def on_lavalink_event(self, event):
        """Track events raised by lavalink"""
        if isinstance(event, lavalink.events.QueueEndEvent):
            await self.connect_to(event.player.guild_id, None)
            self.shiro.lavalink.players.remove(int(event.player.guild_id))

        elif isinstance(event, lavalink.events.TrackStartEvent):
            round = event.player.fetch("round")
            if round is not None:
                event.player.store("round", round + 1)

    async def connect_to(self, guild_id, channel_id):
        """Connects to voice channel, if None disconnects"""
        ws = self.shiro._connection._get_websocket(guild_id)
        await ws.voice_state(str(guild_id), channel_id)

    def enqueue_tracks(self, ctx, tracks):
        """Enqueue all songs"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        for track in tracks:
            player.add(requester=ctx.author.id, track=track)

    async def get_random_tracks(self, ctx, category, amount):
        """Check songs got from database and return tracks"""
        tracks = []
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        songs = self.shiro.get_random_songs(category, amount)

        for song in songs:
            results = await player.node.get_tracks(song["url"])
            if not results or not results["tracks"]:
                self.shiro.sentry.capture_message(f"Invalid Song {song['title']} with URL: {song['url']}")
                continue

            track = results["tracks"][0]
            tracks.append(track)
            history = player.fetch("history")
            history.append(song)
            player.store("history", history)
            print(player.fetch("history"))

        return tracks

    async def fade_volume(self, ctx, fade_in):
        """Fade volume in or out"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        loop_range = range(0, 81, 10) if fade_in else range(80, -1, -10)

        for i in loop_range:
            await player.set_volume(i)
            await asyncio.sleep(0.2)

    def get_song_choices(self, ctx, category):
        """Return songs to be chosen with one correct"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        current_song = player.fetch("history")[player.fetch("round") - 1]
        songs = self.shiro.get_choice_songs(category, current_song["url"])
        songs.append(current_song)
        random.shuffle(songs)
        return songs

    def get_round_winner(self, ctx, songs, message_id):
        """Get the winner who first reacted with the correct song number"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        current_song = player.fetch("history")[player.fetch("round") - 1]
        index = songs.index(current_song)
        reactions = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣"]
        correct_reaction = reactions[index]

        for user_id, reaction in player.fetch("entries")[message_id].items():
            if reaction == correct_reaction:
                return self.shiro.get_user(user_id)

    async def run_round(self, ctx, category):
        """Start a round"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        await player.play()
        song_choices = self.get_song_choices(ctx, category)
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Round {1}/{2}**").format(
            category, player.fetch("round"), len(player.fetch("history"))), description="")

        for index, song in enumerate(song_choices):
            embed.description += f"{emojis[index]} {song['reference']} ‧ {song['title']}\n"

        message = await ctx.send(embed=embed, delete_after=30.5)
        entries = player.fetch("entries")
        entries[message.id] = {}
        player.store("entries", entries)
        await message.add_reaction("1⃣")
        await message.add_reaction("2⃣")
        await message.add_reaction("3⃣")
        await message.add_reaction("4⃣")
        await message.add_reaction("5⃣")

        await self.fade_volume(ctx, True)
        await asyncio.sleep(25)
        await self.fade_volume(ctx, False)

        winner = self.get_round_winner(ctx, song_choices, message.id)
        winner_mention = _("Nobody")
        if winner is not None:
            points = player.fetch("points")
            points.append(winner.id)
            player.store("points", points)
            winner_mention = winner.mention

        song = player.fetch("history")[player.fetch("round") - 1]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Round {1}/{2}**").format(
            category, player.fetch("round"), len(player.fetch("history"))), description="")
        embed.description = _("{0} has won the round!\nSong: [{1} ‧ {2}]({3})").format(
            winner_mention, song["reference"], song["title"], song["url"])
        await ctx.send(embed=embed, delete_after=5)
        await asyncio.sleep(5)

    async def run_quiz(self, ctx, category, rounds):
        """Start a quiz with specified category"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        player.store("ctx", ctx)
        player.store("round", 0)
        player.store("entries", {})
        player.store("points", [])
        player.store("history", [])
        await player.set_volume(0)
        members = ctx.author.voice.channel.members
        member_mentions = " ".join([member.mention for member in members if not member.bot])
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ Starting**").format(category),
                              description=_("Get ready, the quiz will start in 3 seconds!\n{0}").format(member_mentions))
        message = await ctx.send(embed=embed)

        tracks = await self.get_random_tracks(ctx, category, rounds)
        self.enqueue_tracks(ctx, tracks)

        try:
            await message.delete()
        except:
            pass

        while player.queue:
            await self.run_round(ctx, category)

        counted = collections.Counter(player.fetch("points"))
        winners = [self.shiro.get_user(id) for id, points in dict(counted).items() if counted.most_common(1)[0][1] == points]
        winner_mentions = [winner.mention for winner in winners]
        embed = discord.Embed(color=7830745, title=_("**\🎵 {0} quiz ‧ End**").format(category))

        if len(winners) == 0:
            embed.description = _("Nobody won the song quiz! There were {0} round(s).").format(len(player.fetch("history")))
        elif len(winners) == 1:
            embed.description = _("{0} has guessed {1}/{2} songs correctly and won!").format(
                winner_mentions[0], counted.most_common(1)[0][1], len(player.fetch("history")))
        else:
            embed.description = _("{0} have scored a draw with {1}/{2} songs correctly guessed each.").format(
                " & ".join(winner_mentions), counted.most_common(1)[0][1], len(player.fetch("history")))

        await ctx.send(embed=embed)
        await player.skip()

    @commands.command(aliases=["openingquiz", "openings"])
    @commands.check(checks.voice_available)
    async def opquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Guess anime openings with specified amount of rounds\n"""
        await self.run_quiz(ctx, "Opening", rounds)

    @commands.command(aliases=["endingquiz", "endings"])
    @commands.check(checks.voice_available)
    async def edquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Openings are too easy for you? This is next level!"""
        await self.run_quiz(ctx, "Ending", rounds)

    @commands.command(aliases=["osts"])
    @commands.check(checks.voice_available)
    @commands.check(checks.has_voted)
    async def ostquiz(self, ctx, rounds: converters.RangeInt(1, 25) = 10):
        """Guess OST's from Nintendo games!"""
        await self.run_quiz(ctx, "OST", rounds)

    @commands.command(aliases=["end", "skip", "forceskip", "reduce"])
    @commands.check(checks.is_requester)
    @commands.check(checks.player_available)
    async def stop(self, ctx):
        """Stop running quiz or playback"""
        player = self.shiro.lavalink.players.get(ctx.guild.id)
        guild_history_before = list(player.fetch("history"))

        for track in player.queue:
            history = player.fetch("history")
            history.pop(-1)
            player.store("history", history)

        player.queue.clear()
        embed = discord.Embed(color=7830745, title=_("**\🎵 Stop quiz**"))
        if len(guild_history_before) == len(player.fetch("history")):
            embed.description = _("Quiz already ends after this round. Playback will be stopped then.")
        else:
            embed.description = _("Reducing quiz rounds from {0} to {1}. Playback will end after current round.").format(
                len(guild_history_before), len(player.fetch("history")))
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """Reconnect to voice channel if quiz is running"""
        player = self.shiro.lavalink.players.get(member.guild.id)
        if member.id == self.shiro.user.id and player is not None:
            if after.channel is not None and player.current is not None:
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
        player = self.shiro.lavalink.players.get(user.guild.id)
        if not player:
            return

        entries = player.fetch("entries")
        if reaction.message.guild is not None and not user.bot:
            if reaction.message.id in entries:
                if user.id not in entries[reaction.message.id]:
                    entries[reaction.message.id][user.id] = reaction.emoji
                    player.store("entries", entries)


def setup(shiro):
    shiro.add_cog(Songs(shiro))
