"""
Shiro Discord Bot - A fun related anime bot
Copyright (C) 2019 MrSpinne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
from discord.ext import commands
from sentry_sdk import init, capture_exception

from library import exceptions


class Errors(commands.Cog):
    """Output custom messages on command error and perform recovery.

    Parameters
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.

    Attributes
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.
    st_dsn: `str`
        Sentry dsn of account to post stats to.

    """
    def __init__(self, bot):
        self.bot = bot
        self.st_dsn = self.bot.get_config("sentry", "dsn")
        self.init_sentry()

    def init_sentry(self):
        """Initialize connection to Sentry to post errors to.

        This will only be enabled if credentials provided.

        """
        if self.st_dsn:
            init(self.st_dsn)

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Catch all errors on commands an perform actions.

        Parameters
        ----------
        ctx: :obj:`discord.ext.command.Context`
            Context of the command which raised an exception.
        error: :obj:`discord.ext.commands.CommandError`
            Error which was raised.

        """
        if isinstance(error, commands.BotMissingPermissions):
            message = _("Shiro can only execute this command with: {perms}.").format(perms=error.missing_perms)
        elif isinstance(error, exceptions.NotVoted):
            message = _("You have to vote to access this command. [Vote for free]({url})").format(
                url="https://vote.shiro.pro")
        elif isinstance(error, exceptions.NotAscii):
            message = _("You can only use standard characters (ascii), not `{argument}`.").format(
                argument=error.argument)
        elif isinstance(error, exceptions.NotLength):
            message = _("Please use not more than {max_length} characters. `{argument}` is not allowed.").format(
                max_length=error.max_length, argument=error.argument)
        elif isinstance(error, exceptions.NotRestrictedChannel):
            message = _("In this server, commands are restricted to {channel}.").format(
                channel=self.bot.get_channel(error.channel).mention)
        elif isinstance(error, exceptions.NotInVoice):
            message = _("To start listening to music, you have to be in a voice channel (not afk) first.")
        elif isinstance(error, exceptions.NoVoiceAvailable):
            message = _("The bot is already playing in {channel}.").format(channel=error.channel)
        elif isinstance(error, commands.MissingRequiredArgument):
            message = _("Please provide the {argument} to use the command.").format(argument=error.param.name)
        elif isinstance(error, commands.ArgumentParsingError):
            message = _("There was an error parsing your input. "
                        "If you want to use quotation marks, please use `\\\"` instead.")
        elif isinstance(error, commands.CommandNotFound):
            return
        else:
            message = _("An unknown error occurred on command execution. The error has been reported.")
            capture_exception(error)

        embed = discord.Embed(color=10892179)
        embed.set_author(icon_url="https://img.icons8.com/color/48/000000/mongrol.png", name="Test")

        try:
            ctx.send(embed=embed)
        except discord.Forbidden:
            pass


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Errors(bot))
