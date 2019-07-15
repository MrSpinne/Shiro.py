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
                              "`{0}info` ‧ Show credits of the bot and links (e.g. song list)\n"
                              "`{0}request \"<song>\" \"<anime>\" \"<youtube url>\"` ‧"
                              " Request a song for the song quiz").format(ctx.prefix)
        await ctx.author.send(embed=embed, content=_("Here're all commands for **{0}**:").format(ctx.guild.name))

        embed = discord.Embed(color=7830745, title=_("**\👾 Games**"))
        embed.description = _("`{0}songquiz [1-25]` ‧ Guess anime songs with specified amount of rounds").format(
            ctx.prefix)
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
                              "[All songs]({2})").format(owner, "https://discord.gg/QPa75ut", self.shiro.songs_list_url)
        await ctx.send(embed=embed)

    @commands.command(aliases=["songrequest"])
    async def request(self, ctx, title, anime, youtube_url: converters.YoutubeUrl):
        """Request a song for the songquiz"""
        embed = discord.Embed(color=7830745, title="**\⚠️ New song request**")
        embed.description = f"User **{ctx.author.name}#{ctx.author.discriminator}** requested a song."
        embed.add_field(name="Song title", value=title)
        embed.add_field(name="Youtube URL", value=youtube_url)
        embed.add_field(name="Anime", value=anime)
        message = await self.shiro.app_info.owner.send(embed=embed)
        await message.add_reaction("👍🏻")
        await message.add_reaction("👎🏻")

        embed = discord.Embed(color=7830745, title=_("**\📄 Song request**"))
        embed.description = _("You requested the song `{0}` from anime `{1}` to be added into the song quiz. "
                              "Thank you for your support, our bot staff will review it.").format(title, anime)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        """Add song to database if owner accepts"""
        if payload.emoji.name != "👍🏻" and payload.emoji.name != "👎🏻":
            return

        user = self.shiro.get_user(payload.user_id)
        if getattr(user, "id", None) != self.shiro.app_info.owner.id:
            return

        channel = await self.shiro.fetch_channel(payload.channel_id)
        if not isinstance(channel, discord.DMChannel):
            return

        message = await user.fetch_message(payload.message_id)
        if message is None:
            return

        embeds = message.embeds
        if embeds is None:
            return
        if embeds[0].title != "**\⚠️ New song request**":
            return

        if payload.emoji.name == "👍🏻":
            fields = embeds[0].fields
            title = fields[0].value
            youtube_url = fields[1].value
            anime = fields[2].value
            self.shiro.add_song(title, anime, youtube_url)
            await message.add_reaction("✅")
        else:
            await message.add_reaction("❌")


def setup(shiro):
    shiro.add_cog(General(shiro))
