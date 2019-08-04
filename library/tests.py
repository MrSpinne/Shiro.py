import discord
from discord.ext import commands


class Tester:
    def __init__(self, shiro):
        self.shiro = shiro
        self.ctx = None

    async def run(self):
        """Start tests"""
        await self.create_ctx()
        await self.test_commands()
        self.shiro.shutdown()

    async def create_ctx(self):
        """Create fake ctx to invoke commands under"""
        text_channel = self.shiro.get_channel(self.shiro.config["tests"]["text_channel"])
        voice_channel = self.shiro.get_channel(self.shiro.config["tests"]["voice_channel"])
        message = await text_channel.send("Starting tests!")
        message.author.voice.channel = voice_channel
        prefix = await self.shiro.get_prefix(message)
        message.content = "{0}info".format(prefix)
        self.ctx = self.shiro.get_context(message)

    async def test_commands(self):
        """Run tests for every command"""
        for command in self.shiro.walk_commands():
            self.ctx.command = command
            await self.shiro.invoke(self.ctx)
