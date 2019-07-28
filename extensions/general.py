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
                              "`{0}oprequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request opening for quiz\n"
                              "`{0}edrequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request ending for quiz\n"
                              "`{0}ostrequest \"<song>\" \"<anime>\" \"<yt url>\"` ‧ Request OST for quiz"
                              ).format(ctx.prefix)
        await ctx.author.send(embed=embed, content=_("Here're all commands for **{0}**:").format(ctx.guild.name))

        embed = discord.Embed(color=7830745, title=_("**\🎵 Songs**"))
        embed.description = _("`{0}opquiz [1-25]` ‧ Guess anime openings with specified amount of rounds\n"
                              "`{0}edquiz [1-25]` ‧ Openings are too easy for you? This is next level!\n"
                              "`{0}ostquiz [1-25]` ‧ Guess OST's from Nintendo games!\n"
                              "`{0}stop` ‧ Stop running quiz or playback").format(ctx.prefix)
        await ctx.author.send(embed=embed)

        if not checks.is_guild_admin(ctx):
            return

        languages = "/".join(self.shiro.get_languages())
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Settings**"))
        embed.description = _("`{0}prefix <1-10 symbols>` ‧ Change server prefix\n"
                              "`{0}deletion <on/off>` ‧ Enable or disable command message deletion\n"
                              "`{0}channel <none/channel>` ‧ Set channel in which commands are allowed only\n"
                              "`{0}language <{1}>` ‧ Change bot language\n"
                              "`{0}config` ‧ Display current configuration").format(ctx.prefix, languages)
        await ctx.author.send(embed=embed)

        if not checks.is_team_member(ctx):
            return

    @commands.command(aliases=["information", "about", "credits", "spinne", "shiro"])
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

    @commands.command(aliases=["openingrequest", "openingreq", "opreq"])
    async def oprequest(self, ctx, title, anime, yt_url: converters.YoutubeUrl):
        """Request a song for the songquiz"""
        await self.do_request(ctx, title, anime, yt_url, "Opening")

    @commands.command(aliases=["endingrequest", "endingreq", "edreq"])
    async def edrequest(self, ctx, title, anime, yt_url: converters.YoutubeUrl):
        await self.do_request(ctx, title, anime, yt_url, "Ending")

    @commands.command(aliases=["ostreq"])
    async def ostrequest(self, ctx, title, anime, yt_url: converters.YoutubeUrl):
        await self.do_request(ctx, title, anime, yt_url, "OST")

    async def do_request(self, ctx, title, reference, url, category):
        """Request a song for specified category"""
        embed = discord.Embed(color=7830745, title=_("**\📄 {0} request**").format(category))
        embed.description = _("You requested [{0} ‧ {1}]({2}) to be added into the {3} quiz. "
                              "Thank you for your support, our bot staff will review it.").format(title, reference, url, category)
        await ctx.send(embed=embed)

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
            category = fields[2].value
            url = fields[3].value
            self.shiro.add_song(title, reference, url, category)
            await message.add_reaction("✅")
        else:
            await message.add_reaction("❌")


def setup(shiro):
    shiro.add_cog(General(shiro))
