from discord.ext import commands


class NoVoice(commands.CheckFailure):
    """Raised when user is not in voice channel or bot is already in voice channel"""
    pass


class NotInRange(commands.BadArgument):
    """Raised when a number is not in range"""
    def __init__(self, argument, min_int, max_int):
        self.argument = argument
        self.min_int = min_int
        self.max_int = max_int
