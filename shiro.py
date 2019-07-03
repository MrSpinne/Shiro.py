import discord
from discord.ext import commands, tasks

import json
import psycopg2
import asyncio
import pathlib
import sentry_sdk


class Shiro(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix=commands.when_mentioned_or("s."), case_insensitive=True, help_command=None)
		self.credentials = self.load_credentials()
		self.app_info, self.db_connector, self.db_cursor = None, None, None

	async def on_ready(self):
		"""Get ready and initialize"""
		self.app_info = await self.application_info()
		self.clear_cache()
		self.connect_database()
		self.load_all_extensions()
		self.update_status.start()
		print(f"Shiro ready to serve {len(self.users)} users")
		print(2/0)

	def load_credentials(self):
		"""Get credentials from file"""
		with open("credentials.json", "r", encoding="utf-8") as file:
			return json.load(file)

	def clear_cache(self):
		"""Delete all files located in directory"""
		files = [file for file in pathlib.Path("cache").glob("**/*") if file.is_file()]
		for file in files:
			file.unlink()

	def connect_database(self):
		"""Establish connection to postgres database"""
		self.db_connector = psycopg2.connect(**self.credentials["postgres"])
		self.db_cursor = self.db_connector.cursor()

	def disconnect_database(self):
		"""Disconnect from database"""
		if self.db_connector:
			self.db_cursor.close()
			self.db_connector.close()

	def load_all_extensions(self):
		"""Load all extensions from directory"""
		extensions = [file.stem for file in pathlib.Path("extensions").glob("*.py")]
		for extension in extensions:
			self.load_extension(f"extensions.{extension}")

	async def disconnect_voice_clients(self):
		"""Disconnects all voice clients and stops audio"""
		for voice_client in self.voice_clients:
			try:
				voice_client.stop()
			finally:
				await voice_client.disconnect()

	@tasks.loop(minutes=5.0)
	async def update_status(self):
		"""Update status every 5 minutes"""
		while True:
			activity = discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.users)} Usern - s.help")
			await self.change_presence(activity=activity)
			await asyncio.sleep(300)

		# TODO: Add DBL

	async def stop(self):
		"""Stops all processes running and the bot himself"""
		await self.disconnect_voice_clients()
		self.disconnect_database()
		await self.close()
		exit()


shiro = Shiro()
shiro.run(shiro.credentials["discord"]["token"])
sentry_sdk.init(shiro.credentials["sentry"]["public_dsn"])
