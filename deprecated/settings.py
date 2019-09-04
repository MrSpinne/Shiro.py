#  Shiro Discord Bot - A fun related anime bot
#  Copyright (C) 2019 MrSpinne
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <https://www.gnu.org/licenses/>.

import discord
from discord.ext import commands
from library import checks
from deprecated import converters

import typing


class Settings(commands.Cog):
    """Settings cog to change bots behavior per guild"""
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(aliases=["setprefix"])
    @commands.check(checks.is_guild_admin)
    async def prefix(self, ctx, prefix: converters.Prefix):
        """Change guild prefix"""
        self.shiro.set_guild_setting(ctx.guild.id, "prefix", prefix)
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Prefix**"))
        embed.description = _("Server prefix were set to `{0}`. If you forget it, "
                              "you can always use `@Shiro` to get help.")
        embed.description = embed.description.format(prefix)
        await ctx.send(embed=embed)

    @commands.command(aliases=["setdeletion", "commanddeletion", "cmddel", "invocationdeletion"])
    @commands.check(checks.is_guild_admin)
    async def deletion(self, ctx, state: converters.Bool):
        """Enable or disable command message deletion"""
        self.shiro.set_guild_setting(ctx.guild.id, "invocation_deletion", state)
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Command deletion**"))
        embed.description = _("Command message deletion were {0}.").format(_("enabled") if state else _("disabled"))
        await ctx.send(embed=embed)

    @commands.command(aliases=["setchannel", "channelonly", "onechannel", "restrict", "restrictchannel"])
    @commands.check(checks.is_guild_admin)
    async def channel(self, ctx, channel: typing.Union[converters.Nothing, discord.TextChannel]):
        """Set channel in which commands are allowed only"""
        self.shiro.set_guild_setting(ctx.guild.id, "restrict_channel", channel if channel is None else channel.id)
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Channel only**"))
        embed.description = _("Commands can now be executed {0}.").format(
            _("everywhere") if channel is None else _("in channel {0}").format(channel.mention))
        await ctx.send(embed=embed)

    @commands.command(aliases=["setlanguage", "lang"])
    @commands.check(checks.is_guild_admin)
    async def language(self, ctx, language: converters.Language):
        """Set bots language"""
        self.shiro.set_guild_setting(ctx.guild.id, "language", language.alpha_2)
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Language**"))
        embed.description = _("Language were set to `{0}`.").format(language.name)
        await ctx.send(embed=embed)

    @commands.command(aliases=["configuration", "setting", "settings", "option", "options"])
    @commands.check(checks.is_guild_admin)
    async def config(self, ctx):
        """Display current configuration"""
        prefix, invocation_deletion, restrict_channel, language = self.get_formatted_guild_settings(ctx)
        embed = discord.Embed(color=7830745, title=_("**\\⚙️ Config**"))
        embed.description = _("Prefix ‧ `{0}`\nInvocation deletion ‧ `{1}`\nRestrict channel ‧ {2}\nLanguage ‧ `{3}`").format(
            prefix, invocation_deletion, restrict_channel, language)
        await ctx.send(embed=embed)

    def get_formatted_guild_settings(self, ctx):
        """Get the guild settings and format them"""
        prefix = self.shiro.get_guild_setting(ctx.guild.id, "prefix")
        invocation_deletion = _("enabled") if self.shiro.get_guild_setting(ctx.guild.id, "invocation_deletion") is True else _("disabled")
        restrict_channel = self.shiro.get_channel(self.shiro.get_guild_setting(ctx.guild.id, "restrict_channel"))
        restrict_channel = _("`disabled`") if restrict_channel is None else restrict_channel.mention
        language = self.shiro.get_guild_setting(ctx.guild.id, "language")

        return prefix, invocation_deletion, restrict_channel, language


def setup(shiro):
    shiro.add_cog(Settings(shiro))
