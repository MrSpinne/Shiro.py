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

from discord.ext import commands

from library import exceptions


class Ascii(commands.Converter):
    """Checks if a string is ascii only.

    This won't convert anything.

    """

    async def convert(self, ctx, argument):
        """Check the argument for non ascii symbols.

        Parameters
        ----------
        ctx: :obj:`discord.Context`
            Context the command was invoked with.
        argument: :obj:`str`
            Argument that have been passed to the converter.

        Returns
        -------
        str
            Returns the argument if check has been passed.

        Raises
        ------
        exceptions.NotAscii
            Raised if argument is not ascii.

        """
        if all(ord(c) < 128 for c in argument):
            return argument

        raise exceptions.NotAscii(argument)


class Length(commands.Converter):
    """Check if a string is not longer than specified.

    Parameters
    ----------
    max_length: `int`
        Max length of the string that is allowed.

    """

    def __init__(self, max_length):
        self.max_length = max_length

    async def convert(self, ctx, argument):
        """Check if the argument is not longer than specified.

        Parameters
        ----------
        ctx: :obj:`discord.Context`
            Context the command was invoked with.
        argument: :obj:`str`
            Argument that have been passed to the converter.

        Returns
        -------
        str
            Returns the argument if check has passed.

        Raises
        ------
        exceptions.NotLength
            Raised if argument is longer than specified.

        """
        if len(argument) <= self.max_length:
            return argument

        raise exceptions.NotLength(argument, self.max_length)


class Prefix(commands.Converter):
    """Check if an argument mets the requirements to be set as a prefix.

    A prefix should be ascii and not longer than 10 characters.

    """

    async def convert(self, ctx, argument):
        """Use ascii and length converter to check.

        Parameters
        ----------
        ctx: :obj:`discord.Context`
            Context the command was invoked with.
        argument: :obj:`str`
            Argument that have been passed to the converter.

        Returns
        -------
        str
            Returns the argument if check has passed.

        """
        argument = await Ascii.convert(ctx, argument)
        argument = await Length(10).convert(ctx, argument)
        return argument
