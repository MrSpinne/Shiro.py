from discord.ext import commands


class NoVoice(commands.CheckFailure):
    """Raised when user is not in voice channel or bot is already in voice channel"""
    pass


class NotGuildOwner(commands.CheckFailure):
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
