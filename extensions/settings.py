import typing

import discord
from discord.ext import commands

from library import checks, converters


class Settings(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["setprefix"])
    @commands.check(checks.is_guild_owner)
    async def prefix(self, ctx, prefix: converters.LengthStr(1, 10)):
        """Change  guild prefix"""
        self.shiro.set_guild_setting(ctx.guild.id, "prefix", prefix)
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Prefix**"))
        embed.description = _(
            "Server prefix were set to `{0}`. If you forget it, you can always use `@Shiro` to get help.")
        embed.description = embed.description.format(prefix)
        await ctx.send(embed=embed)

    @commands.command(aliases=["setdeletion", "commanddeletion", "cmddel"])
    @commands.check(checks.is_guild_owner)
    async def deletion(self, ctx, state: converters.Bool):
        """Enable or disable command message deletion"""
        self.shiro.set_guild_setting(ctx.guild.id, "command_deletion", state)
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Command deletion**"))
        embed.description = _("Command message deletion were {0}.").format("enabled" if state else "disabled")
        await ctx.send(embed=embed)

    @commands.command(aliases=["setchannel", "channelonly", "onechannel"])
    @commands.check(checks.is_guild_owner)
    async def channel(self, ctx, channel: typing.Union[converters.Nothing, discord.TextChannel]):
        """Set channel in which commands are allowed only"""
        self.shiro.set_guild_setting(ctx.guild.id, "channel_only", channel if channel is None else channel.id)
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Channel only**"))
        embed.description = _("Commands can now be executed {0}.").format(
            _("everywhere") if channel is None else _("in channel {0}").format(channel.mention))
        await ctx.send(embed=embed)

    @commands.command(aliases=["setlanguage", "lang"])
    @commands.check(checks.is_guild_owner)
    async def language(self, ctx, language: converters.Language):
        """Set bots language"""
        self.shiro.set_guild_setting(ctx.guild.id, "language", language)
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Language**"))
        embed.description = _("Language were set to `{0}`.").format(language)
        await ctx.send(embed=embed)

    @commands.command(aliases=["configuration", "setting", "settings", "option", "options"])
    @commands.check(checks.is_guild_owner)
    async def config(self, ctx):
        """Display current configuration"""
        prefix, command_deletion, channel_only, language = self.get_formatted_guild_settings(ctx)
        embed = discord.Embed(color=7830745, title=_("**\⚙️ Config**"))
        embed.description = _("Prefix ‧ `{0}`\nCommand deletion ‧ `{1}`\nChannel only ‧ {2}\nLanguage ‧ `{3}`")
        embed.description = embed.description.format(prefix, command_deletion, channel_only, language)
        await ctx.send(embed=embed)

    def get_formatted_guild_settings(self, ctx):
        """Get the guild settings and format them"""
        prefix = self.shiro.get_guild_setting(ctx.guild.id, "prefix")
        command_deletion = _("enabled") if self.shiro.get_guild_setting(ctx.guild.id, "command_deletion") is True else _("disabled")
        channel_only = self.shiro.get_channel(self.shiro.get_guild_setting(ctx.guild.id, "channel_only"))
        channel_only = _("`disabled`") if channel_only is None else channel_only.mention
        language = self.shiro.get_guild_setting(ctx.guild.id, "language")

        return prefix, command_deletion, channel_only, language


def setup(shiro):
    shiro.add_cog(Settings(shiro))
