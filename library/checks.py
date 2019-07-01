from discord.ext import commands
from library import exceptions


def voice_available():
    """Checks if voice client and voice user is available"""
    def predicate(ctx):
        if ctx.author.voice is not None:
            if not ctx.author.voice.afk:
                if ctx.voice_client is None:
                    return True
        raise exceptions.NoVoice
    return commands.check(predicate)
