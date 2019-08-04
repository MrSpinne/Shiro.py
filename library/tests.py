import discord
from discord.ext import commands


class Tester:
    def __init__(self, shiro):
        self.shiro = shiro

    def create_ctx(self):
        """Create ctx to invoke commands under"""
        text_channel = self.shiro.get_channel(self.shiro.config["tests"]["text_channel"])
        voice_channel = self.shiro.get_channel(self.shiro.config["tests"]["voice_channel"])
        message = discord.Message()

    async def run(self):
        """Start tests"""
        self.create_ctx()
        await self.test_commands()

    async def test_commands(self):
        """Run tests for every command"""



        for command in self.shiro.walk_commands():
            pass
