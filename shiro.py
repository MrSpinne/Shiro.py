import discord
from discord.ext import commands, tasks
from library import exceptions, checks

import json
import psycopg2.extras
import asyncio
import pathlib
import time
import inspect
import gettext
import builtins
import sentry_sdk.integrations.aiohttp


class Shiro(commands.Bot):
	def __init__(self):
		super().__init__(command_prefix=commands.when_mentioned, case_insensitive=True, help_command=None)
		builtins.__dict__["_"] = self.translate
		self.credentials, self.db_connector, self.db_cursor, self.app_info, self.sentry = None, None, None, None, sentry_sdk
		self.startup()

	def startup(self):
		"""Prepare start"""
		self.log("Starting Shiro...")
		self.credentials = self.load_credentials()
		self.sentry.init(dsn=self.credentials["sentry"]["dsn"], integrations=[self.sentry.integrations.aiohttp.AioHttpIntegration()])
		self.clear_cache()
		self.connect_database()
		self.add_command_handlers()
		self.load_all_extensions()

	def translate(self, string):
		"""Translate string to language of ctx got from frame (commands only)"""
		language = "en"

		outer_frames = inspect.getouterframes(inspect.currentframe())
		for frame in outer_frames:
			arguments = inspect.getargvalues(frame.frame)
			if "ctx" in arguments.locals:
				if arguments.locals["ctx"].guild is not None:
					guild_id = arguments.locals["ctx"].guild.id
					language = self.get_guild_setting(guild_id, "language")
					break

		try:
			translation = gettext.translation("base", "locales/", [language]).gettext(string)
		except:
			translation = string
			self.log(f"Error localizing string \"{string}\" for language \"{language}\"", "error")

		return translation

	def load_credentials(self):
		"""Get credentials from file"""
		self.log("Loading credentials...")
		with open("data/credentials.json", "r", encoding="utf-8") as file:
			return json.load(file)

	def clear_cache(self):
		"""Delete all files located in cache directory"""
		self.log("Clearing cache...")
		files = [file for file in pathlib.Path("cache").glob("**/*") if file.is_file()]
		for file in files:
			file.unlink()

	def connect_database(self):
		"""Establish connection to postgres database"""
		self.log("Connecting to database...")
		self.db_connector = psycopg2.connect(**self.credentials["postgres"])
		self.db_cursor = self.db_connector.cursor(cursor_factory=psycopg2.extras.DictCursor)

	def disconnect_database(self):
		"""Disconnect from database"""
		self.log("Disconnecting from database...")
		if self.db_connector:
			self.db_cursor.close()
			self.db_connector.close()

	def register_guild(self, guild_id):
		"""Register guild to database if it is not already registered"""
		sql = f"INSERT INTO public.guilds (id) VALUES ({guild_id}) ON CONFLICT DO NOTHING"
		self.db_cursor.execute(sql)
		self.db_connector.commit()

	def unregister_guild(self, guild_id):
		"""Unregister guild from database with all settings"""
		sql = f"DELETE FROM public.guilds WHERE id = {guild_id}"
		self.db_cursor.execute(sql)
		self.db_connector.commit()

	def update_guilds(self):
		"""Add or remove guilds from database to prevent bugs"""
		self.log("Updating guilds in database...")
		for guild in self.guilds:
			self.register_guild(guild.id)

		sql = "SELECT id FROM public.guilds"
		self.db_cursor.execute(sql)
		for guild_id in self.db_cursor.fetchall():
			if self.get_guild(guild_id["id"]) not in self.guilds:
				self.unregister_guild(guild_id)

	def add_command_handlers(self):
		"""Add global command checks and invoke hooks"""
		self.add_check(checks.guild_only)
		self.add_check(checks.channel_only)
		self.add_check(checks.bot_has_permissions)
		self.before_invoke(self.delete_command)

	def load_all_extensions(self):
		"""Load all extensions from directory"""
		self.log("Loading extensions...")
		extensions = [file.stem for file in pathlib.Path("extensions").glob("*.py")]
		for extension in extensions:
			self.load_extension(f"extensions.{extension}")

	def log(self, message, level="info"):
		"""Log activity to console"""
		async def task():
			print(f"[{time.strftime('%H:%M:%S', time.gmtime())}] [{level.upper()}] {message}")

			if level.lower() == "error" and self.app_info is not None:
				embed = discord.Embed(color=10892179, title="Internal Log", description=f"`{message}`")
				await self.app_info.owner.send(embed=embed)

			with open("data/log.txt", "a+", encoding="utf-8") as file:
				file.write(f"[{time.strftime('%d-%m-%Y %H:%M:%S', time.gmtime())}] [{level.upper()}] {message}\n")

		self.loop.create_task(task())

	def get_guild_setting(self, guild_id, setting):
		"""Get guild setting from database"""
		sql = f"SELECT {setting} FROM public.guilds WHERE id = {guild_id}"
		self.db_cursor.execute(sql)
		return self.db_cursor.fetchone()[0]

	async def on_ready(self):
		"""Get ready and start"""
		self.app_info = await self.application_info()
		self.update_guilds()
		self.update_status.start()
		self.log(f"Shiro ready to serve {len(self.users)} users")

	async def delete_command(self, ctx):
		"""Delete command if enabled in guild settings"""
		if self.get_guild_setting(ctx.guild.id, "command_deletion") is True:
			await ctx.message.delete()

	async def shutdown(self):
		"""Stops all processes running and the bot himself"""
		self.disconnect_database()
		self.log("Exiting Shiro...")
		await self.close()

	async def get_prefix(self, message):
		"""Return the prefix which the guild has set"""
		if message.guild is not None and self.app_info is not None:
			return commands.when_mentioned_or(self.get_guild_setting(message.guild.id, "prefix"))(self, message)

		return commands.when_mentioned_or("s.")(self, message)

	async def on_guild_join(self, guild):
		"""Add new guild to database on join"""
		self.register_guild(guild.id)
		self.log(f"Guild \"{guild.name}\" ({guild.id}) joined")

	async def on_guild_remove(self, guild):
		"""Remove guild from database on leave"""
		self.unregister_guild(guild.id)
		self.log(f"Guild \"{guild.name}\" ({guild.id}) left")

	async def on_command_error(self, ctx, error):
		"""Catch errors on command execution"""
		embed = discord.Embed(color=10892179, title=_("**Error on command**"))

		if isinstance(error, commands.MissingRequiredArgument):
			embed.description = _("The command `{0}` is missing the argument `{1}`.")\
				.format(ctx.message.content, error.param.name)
		elif isinstance(error, exceptions.NotInRange):
			embed.description = _("The command `{0}` only takes arguments in range `{1}-{2}`, not `{3}`.")\
				.format(ctx.message.content, error.min_int, error.max_int, error.argument)
		elif isinstance(error, commands.ConversionError) or isinstance(error, commands.BadArgument):
			embed.description = _("A wrong argument were passed into the command `{0}`.")\
				.format(ctx.message.content)
		elif isinstance(error, commands.CommandNotFound) or isinstance(error, commands.NotOwner):
			embed.description = _("The command `{0}` wasn't found. To get a list of command use `{1}`.")\
				.format(ctx.message.content, f"{ctx.prefix}help")
		elif isinstance(error, exceptions.NotGuildOwner):
			embed.description = _("The command `{0}` can only be executed by server owners.")\
				.format(ctx.message.content)
		elif isinstance(error, exceptions.NoVoice):
			embed.description = _("To use the command `{0}` you have to be in an voice channel (not afk). "
			                      "Also, the bot has to be disconnect from voice.")\
				.format(ctx.message.content)
		elif isinstance(error, exceptions.SpecificChannelOnly):
			embed.description = _("On this server commands can only be executed in channel {0}.")\
				.format(error.channel.mention)
		elif isinstance(error, commands.NoPrivateMessage):
			pass
		elif isinstance(error, commands.BotMissingPermissions):
			embed.description = _("The bot is missing permissions to execute commands: `{0}`")\
				.format(", ".join(error.missing_perms))
		elif isinstance(error, commands.CheckFailure):
			embed.description = _("You're lacking permission to execute command `{0}`.")\
				.format(ctx.message.content)
		else:
			embed.description = _("An unknown error occured on command `{0}`. We're going to fix that soon!")\
				.format(ctx.message.content)
			sentry_sdk.capture_exception(error)

		if not isinstance(error, commands.BotMissingPermissions):
			await ctx.send(embed=embed)
		elif (isinstance(error, commands.BotMissingPermissions) and "send_messages" not in error.missing_perms) or \
				(isinstance(error, commands.BotMissingPermissions) and "embed_links" not in error.missing_perms):
			await ctx.send(embed=embed)

	@tasks.loop(minutes=5)
	async def update_status(self):
		"""Update status every 5 minutes"""
		while True:
			activity = discord.Activity(type=discord.ActivityType.listening, name=f"{len(self.users)} Users")
			await self.change_presence(activity=activity)
			await asyncio.sleep(300)
		# TODO: Add DBL


shiro = Shiro()
shiro.run(shiro.credentials["discord"]["token"])
