from discord.ext import commands


class NoVoice(commands.CheckFailure):
    """Raised when user is not in voice channel or bot is already in voice channel"""
    pass
