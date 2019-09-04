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


class NotGuildAdmin(commands.CheckFailure):
    """Raised when user isn't a guild admin.

    Guild owners will always have administrator permissions.

    """


class NotVoted(commands.CheckFailure):
    """Raised when user has not voted.

    Also the bot has to run at least 12 hours to activate vote locking.

    """


class NotAscii(commands.ConversionError):
    """Raised when the argument is not ascii.

    Parameters
    ----------
    argument: `str`
        Argument that could not be converted.

    """

    def __init__(self, argument):
        self.argument = argument


class NotLength(commands.ConversionError):
    """Raised when the argument is longer than expected.

    Parameters
    ----------
    argument: `str`
        Argument that could not be converted.
    max_length: `int`
        Allowed max length of the string.

    """

    def __init__(self, argument, max_length):
        self.argument = argument
        self.max_length = max_length


class NotRestrictedChannel(commands.ConversionError):
    """Raised when the channel is not the restricted channel.

    Parameters
    ----------
    channel: `int`
        The channel commands are only allowed.

    """

    def __init__(self, channel):
        self.channel = channel


class NotInVoice(commands.CheckFailure):
    """Raised when user is not in a voice channel.

    Afk channel included.

    """


class NoVoiceAvailable(commands.CheckFailure):
    """Raised if the bot is not available to play songs.

    Parameters
    ----------
    channel: `str`
        Mention of the channel the bot is already in.

    """

    def __init__(self, channel):
        self.channel = channel


# Old


class NoVoice(commands.CheckFailure):
    """Raised when user is not in voice channel or bot is already in voice channel"""


class NoPlayer(commands.CheckFailure):
    """Raised when no player is existing"""


class NotGuildAdmin(commands.CheckFailure):
    """Raised when user is not the owner of the guild"""


class SpecificChannelOnly(commands.CheckFailure):
    """Raised when an prohibited channel is used"""
    def __init__(self, channel):
        self.channel = channel


class NotVoted(commands.CheckFailure):
    """Raised when user hasn't voted on dbl"""


class NotRequester(commands.CheckFailure):
    """Raised when user isn't requester of the song or isn't admin"""


class NotTeam(commands.CheckFailure):
    """Raised when user isn't a team member"""


class NotInRange(commands.BadArgument):
    """Raised when a number is not in range"""
    def __init__(self, argument, min_int, max_int):
        self.argument = argument
        self.min_int = min_int
        self.max_int = max_int


class NotLengthStr(commands.BadArgument):
    """Raised when string is longer than expected"""
    def __init__(self, argument, max_len):
        self.argument = argument
        self.max_len = max_len


class NotPrefix(commands.BadArgument):
    """Raised when string is not in length"""
    def __init__(self, argument):
        self.argument = argument


class NotBool(commands.BadArgument):
    """Raised when a string is not the specified bool"""
    def __init__(self, argument):
        self.argument = argument


class NotNothing(commands.BadArgument):
    """Raised when a string is not meant to be None"""
    def __init__(self, argument):
        self.argument = argument


class NotLanguage(commands.BadArgument):
    """Raised when a string is not an available language"""
    def __init__(self, argument, available_languages):
        self.argument = argument
        self.available_languages = available_languages


class NotYoutubeURL(commands.BadArgument):
    """Raised when a string is not a valid youtube url"""
    def __init__(self, argument):
        self.argument = argument


class NotAnime(commands.BadArgument):
    """Raised when no anime can be found matching argument"""
    def __init__(self, argument):
        self.argument = argument


class NotSongID(commands.BadArgument):
    """Raised when song doesn't exist in database"""
    def __init__(self, argument):
        self.argument = argument


class NotCategory(commands.BadArgument):
    """Raised when category isn't valid"""
    def __init__(self, argument):
        self.argument = argument
