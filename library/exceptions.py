from discord.ext import commands


class NoVoice(commands.CheckFailure):
    """Raised when user is not in voice channel or bot is already in voice channel"""
    pass


class NoPlayer(commands.CheckFailure):
    """Raised when no player is existing"""
    pass


class NotGuildAdmin(commands.CheckFailure):
    """Raised when user is not the owner of the guild"""
    pass


class SpecificChannelOnly(commands.CheckFailure):
    """Raised when an prohibited channel is used"""
    def __init__(self, channel):
        self.channel = channel


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
    def __init__(self, argument, bool):
        self.argument = argument
        self.bool = bool


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


class NotSongID(commands.CheckFailure):
    def __int__(self, argument):
        self.argument = argument


class NotVoted(commands.CheckFailure):
    """Raised when user hasn't voted on dbl"""
    pass


class NotRequester(commands.CheckFailure):
    """Raised when user isn't requester of the song or isn't admin"""
    pass


class NotTeamMember(commands.CheckFailure):
    """Raised when user isn't a team member"""
    pass
