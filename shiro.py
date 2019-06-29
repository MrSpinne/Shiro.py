import discord
from discord.ext import commands, tasks

import asyncio
import pathlib


class Shiro(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix="s.", case_insensitive=True, help_command=None)

	async def on_ready(self):
		"""Get ready and initialize"""
		self.load_all_extensions()
		self.update_status.start()
		print(f"Shiro ready to serve {len(self.users)} users")

	def load_all_extensions(self):
		"""Load all extensions from directory"""
		extensions = [file.stem for file in pathlib.Path("extensions").glob("*.py")]
		for extension in extensions:
			self.load_extension(f"extensions.{extension}")

	@tasks.loop(minutes=5.0)
	async def update_status(self):
		"""Update status every 5 minutes"""
		while True:
			activity = discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.users)} Usern - s.help")
			await self.change_presence(activity=activity)
			await asyncio.sleep(300)

		# TODO: Add DBL


shiro = Shiro()
shiro.run("NTkzMTE2NzAxMjgxNzQ2OTU1.XRJPiA.uH6TElEihG2KfwyD1jcZhkwF-qc")
