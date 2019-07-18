import discord
from discord.ext import commands
from library import checks, converters

import asyncio


class General(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["?", "cmd", "cmds", "command", "commands"])
    async def help(self, ctx):
        """Display all commands"""
        embed = discord.Embed(color=7830745, title=_("**\📄 General**"))
        embed.description = _("`{0}help` ‧ Display all commands\n"
                              "`{0}info` ‧ Show credits of the bot and links (e.g. support server)\n"
                              "`{0}openingrequest \"<song>\" \"<anime>\" \"<youtube url>\"` ‧ Request opening for quiz\n"
                              "`{0}endingrequest \"<song>\" \"<anime>\" \"<youtube url>\"` ‧ Request ending for quiz"
                              ).format(ctx.prefix)
        await ctx.author.send(embed=embed, content=_("Here're all commands for **{0}**:").format(ctx.guild.name))

        embed = discord.Embed(color=7830745, title=_("**\🎵 Songs**"))
        embed.description = _("`{0}openingquiz [1-25]` ‧ Guess anime openings with specified amount of rounds\n"
                              "`{0}endingquiz [1-25]` ‧ Openings are too easy for you? This is next level!\n"
                              "`{0}stop` ‧ Stop running quiz or playback").format(ctx.prefix)
        await ctx.author.send(embed=embed)

        if ctx.author is not ctx.guild.owner:
            return

        languages = "/".join(self.shiro.get_languages())
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Settings**"))
        embed.description = _("`{0}prefix <1-10 symbols>` ‧ Change server prefix\n"
                              "`{0}deletion <on/off>` ‧ Enable or disable command message deletion\n"
                              "`{0}channel <none/channel>` ‧ Set channel in which commands are allowed only\n"
                              "`{0}language <{1}>` ‧ Change bot language\n"
                              "`{0}config` ‧ Display current configuration").format(ctx.prefix, languages)
        await ctx.author.send(embed=embed)

    @commands.command(aliases=["credits", "about"])
    async def info(self, ctx):
        """Show credits of the bot"""
        owner = f"{self.shiro.app_info.owner.name}#{self.shiro.app_info.owner.discriminator}"
        embed = discord.Embed(color=7830745, title=_("**\📄 About Shiro**"))
        embed.set_thumbnail(url=self.shiro.app_info.owner.avatar_url)
        embed.description = _("Shiro were made by **{0}** in Python. If you have any questions, feel free "
                              "to contact.\n\n[Support & Feedback]({1}) ‧ [Help translate]({1}) ‧ "
                              "[Vote]({2}) ‧ [All songs]({3})").format(
            owner, "https://discord.gg/5z4z8kh", "https://discordbots.org/bot/593116701281746955/vote", self.shiro.songs_list_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["oprequest", "requestopening"])
    async def openingrequest(self, ctx, title, anime, youtube_url: converters.YoutubeUrl):
        """Request a song for the songquiz"""
        await self.do_request(ctx, title, anime, youtube_url, "Opening")
        embed = discord.Embed(color=7830745, title=_("**\📄 Opening request**"))
        embed.description = _("You requested the opening `{0}` from anime `{1}` to be added into the song quiz. "
                              "Thank you for your support, our bot staff will review it.").format(title, anime)
        await ctx.send(embed=embed)

    @commands.command(aliases=["endrequest", "requestending"])
    async def endingrequest(self, ctx, title, anime, youtube_url: converters.YoutubeUrl):
        await self.do_request(ctx, title, anime, youtube_url, "Ending")
        embed = discord.Embed(color=7830745, title=_("**\📄 Ending request**"))
        embed.description = _("You requested the ending `{0}` from anime `{1}` to be added into the song quiz. "
                              "Thank you for your support, our bot staff will review it.").format(title, anime)
        await ctx.send(embed=embed)

    async def do_request(self, ctx, title, reference, url, category):
        """Request a song for specified category"""
        embed = discord.Embed(color=7830745, title="**\⚠️ New song request**")
        embed.description = f"User **{ctx.author.name}#{ctx.author.discriminator}** requested a song."
        embed.add_field(name="Title", value=title)
        embed.add_field(name="Reference", value=reference)
        embed.add_field(name="Category", value=category)
        embed.add_field(name="URL", value=url)
        message = await self.shiro.get_channel(601374759724384272).send(embed=embed)
        await message.add_reaction("👍🏻")
        await message.add_reaction("👎🏻")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Add song to database if owner accepts"""
        if payload.emoji.name != "👍🏻" and payload.emoji.name != "👎🏻":
            return

        if payload.channel_id != 601374759724384272:
            return

        user = self.shiro.get_user(payload.user_id)
        if user.bot:
            return

        channel = self.shiro.get_channel(payload.channel_id)
        message = await channel.fetch_message(payload.message_id)
        if message is None:
            return

        emojis = [reaction.emoji for reaction in message.reactions]

        if "✅" in emojis or "❌" in emojis:
            return

        embeds = message.embeds
        if embeds is None:
            return
        if embeds[0].title != "**\⚠️ New song request**":
            return

        if payload.emoji.name == "👍🏻":
            fields = embeds[0].fields
            title = fields[0].value
            reference = fields[1].value
            category = fields[2].value.lower()
            url = fields[3].value
            self.shiro.add_song(title, reference, url, category)
            await message.add_reaction("✅")
        else:
            await message.add_reaction("❌")


def setup(shiro):
    shiro.add_cog(General(shiro))
