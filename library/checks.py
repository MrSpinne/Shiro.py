from discord.ext import commands


def voice_available():
    def predicate(ctx):
        if ctx.author.voice is not None:
            if not ctx.author.voice.afk:
                if ctx.voice_client is None:
                    return True
        return False
    return commands.check(predicate)
