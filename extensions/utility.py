import discord
from discord.ext import commands
from library import checks

import psutil
import time


class Utility(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command()
    @commands.check(checks.is_bot_owner)
    async def restart(self, ctx):
        """Stops the bot and closes connection"""
        embed = discord.Embed(color=7830745, title=_("**\⚠️ Restarting bot**"))
        embed.description = _("Bot is going to be restartet.")
        await ctx.send(embed=embed)
        await self.shiro.shutdown()

    @commands.command()
    @commands.check(checks.is_bot_owner)
    async def status(self, ctx):
        """Show current bot stats"""
        ping = time.monotonic()
        await self.shiro.application_info()
        ping = int((time.monotonic() - ping) * 1000)

        embed = discord.Embed(color=7830745, title=_("**\⚠️ Status**"))
        embed.description = _("Users: {0}\nServers: {1}\nPlayers: {2}\n"
                              "CPU usage: {3}%\nRAM usage: {4}%\nPing: {5}ms").format(
            len(self.shiro.users), len(self.shiro.guilds), len(self.shiro.lavalink.players),
            psutil.cpu_percent(), psutil.virtual_memory().percent, ping)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.check(checks.is_bot_owner)
    async def evaluate(self, ctx, *, string):
        value = eval(string)
        embed = discord.Embed(color=7830745, title=_("**\⚠️ Evaluation**"))
        embed.description = f"```{value}```"
        await ctx.send(embed=embed)


def setup(shiro):
    shiro.add_cog(Utility(shiro))
