import discord
from discord.ext import commands, tasks
from library import exceptions, checks

import json
import psycopg2.extras
import psycopg2.sql
import asyncio
import pathlib
import inspect
import gettext
import builtins
import sentry_sdk.integrations.aiohttp
import logging
import dbl
import pbwrap


class Shiro(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, case_insensitive=True, help_command=None)
        builtins.__dict__["_"] = self.translate
        self.credentials, self.db_connector, self.db_cursor, self.app_info = None, None, None, None
        self.sentry, self.songs_list_url = sentry_sdk, None
        self.startup()

    def startup(self):
        """Prepare start"""
        logging.basicConfig(level=logging.INFO)
        self.credentials = self.load_credentials()
        self.sentry.init(dsn=self.credentials["sentry"]["dsn"],
                         integrations=[self.sentry.integrations.aiohttp.AioHttpIntegration()])
        self.clear_cache()
        self.connect_database()
        self.add_command_handlers()
        self.update_songs_list.start()
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
            translation = gettext.translation("base", "locales/", [language], codeset="utf-8").gettext(string)
        except Exception as error:
            translation = string
            logging.warning(error)
            self.sentry.capture_exception(error)

        return translation

    def load_credentials(self):
        """Get credentials from file"""
        with open("data/credentials.json", "r", encoding="utf-8") as file:
            return json.load(file)

    def clear_cache(self):
        """Delete all files located in cache directory"""
        files = [file for file in pathlib.Path("cache").glob("**/*") if file.is_file()]
        for file in files:
            file.unlink()

    def connect_database(self):
        """Establish connection to postgres database"""
        self.db_connector = psycopg2.connect(**self.credentials["postgres"])
        self.db_cursor = self.db_connector.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def disconnect_database(self):
        """Disconnect from database"""
        if self.db_connector:
            self.db_cursor.close()
            self.db_connector.close()

    def register_guild(self, guild_id):
        """Register guild to database if it is not already registered"""
        sql = psycopg2.sql.SQL("INSERT INTO public.guilds (id) VALUES (%s) ON CONFLICT DO NOTHING")
        self.db_cursor.execute(sql, [guild_id])
        self.db_connector.commit()

    def unregister_guild(self, guild_id):
        """Unregister guild from database with all settings"""
        sql = psycopg2.sql.SQL("DELETE FROM public.guilds WHERE id = %s")
        self.db_cursor.execute(sql, [guild_id])
        self.db_connector.commit()

    def update_guilds(self):
        """Add or remove guilds from database to prevent bugs"""
        for guild in self.guilds:
            self.register_guild(guild.id)

        sql = psycopg2.sql.SQL("SELECT id FROM public.guilds")
        self.db_cursor.execute(sql)
        for guild_id in self.db_cursor.fetchall():
            if self.get_guild(guild_id["id"]) not in self.guilds:
                self.unregister_guild(guild_id["id"])

    def add_command_handlers(self):
        """Add global command checks and command invokes"""
        self.add_check(checks.guild_only)
        self.add_check(checks.channel_only)
        self.add_check(checks.bot_has_permissions)
        self.before_invoke(self.delete_command)

    def load_all_extensions(self):
        """Load all extensions from directory"""
        extensions = [file.stem for file in pathlib.Path("extensions").glob("*.py")]
        for extension in extensions:
            self.load_extension(f"extensions.{extension}")

    def get_guild_setting(self, guild_id, setting):
        """Get guild setting from database"""
        sql = psycopg2.sql.SQL("SELECT {} FROM public.guilds WHERE id = %s").format(psycopg2.sql.Identifier(setting))
        self.db_cursor.execute(sql, [guild_id])
        return self.db_cursor.fetchone()[0]

    def set_guild_setting(self, guild_id, setting, value):
        """Set guild setting in database to specified value"""
        sql = psycopg2.sql.SQL("UPDATE public.guilds SET {} = %s WHERE id = %s").format(
            psycopg2.sql.Identifier(setting))
        self.db_cursor.execute(sql, [value, guild_id])
        self.db_connector.commit()

    def get_random_songs(self):
        """Get 5 random songs from database"""
        sql = psycopg2.sql.SQL("SELECT title, anime, youtube_url FROM public.songs ORDER BY RANDOM() LIMIT 5")
        self.db_cursor.execute(sql)
        return self.db_cursor.fetchall()

    def get_all_songs(self):
        """Get all songs from database in alphabetic order"""
        sql = psycopg2.sql.SQL("SELECT title, anime, youtube_url FROM public.songs ORDER BY anime ASC")
        self.db_cursor.execute(sql)
        return self.db_cursor.fetchall()

    def add_song(self, title, anime, youtube_url):
        """Add a song to the database"""
        sql = psycopg2.sql.SQL("INSERT INTO public.songs (title, anime, youtube_url) VALUES (%s, %s, %s)")
        self.db_cursor.execute(sql, [title, anime, youtube_url])
        self.db_connector.commit()

    def get_languages(self):
        """Get all languages found in locales"""
        languages = [item.name for item in pathlib.Path("locales").iterdir() if item.is_dir()]
        return languages

    async def on_ready(self):
        """Get ready and start"""
        self.app_info = await self.application_info()
        self.update_guilds()
        self.update_status.start()
        logging.info(f"Ready to serve {len(self.users)} users in {len(self.guilds)} guilds")

    async def delete_command(self, ctx):
        """Delete command if enabled in guild settings"""
        if ctx.guild is not None:
            if self.get_guild_setting(ctx.guild.id, "command_deletion") is True:
                await ctx.message.delete()

    async def on_message(self, message):
        """Send help if bot is mentioned"""
        if self.user in message.mentions and message.guild is not None:
            ctx = await self.get_context(message)
            ctx.prefix = self.get_guild_setting(message.guild.id, "prefix")
            ctx.command = self.get_command("help")
            await self.invoke(ctx)

        await self.process_commands(message)

    async def shutdown(self):
        """Stops all processes running and the bot himself"""
        self.disconnect_database()
        await self.close()

    async def get_prefix(self, message):
        """Return the prefix which the guild has set"""
        if message.guild is not None and self.app_info is not None:
            return self.get_guild_setting(message.guild.id, "prefix")

        return "s."

    async def on_guild_join(self, guild):
        """Add new guild to database on join"""
        self.register_guild(guild.id)

    async def on_guild_remove(self, guild):
        """Remove guild from database on leave"""
        self.unregister_guild(guild.id)

    async def on_command_error(self, ctx, error):
        """Catch errors on command execution"""
        embed = discord.Embed(color=10892179, title=_("\❌ **Error on command**"))

        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = _("The command `{0}` is missing the `{1}`.") \
                .format(ctx.message.content, error.param.name)
        elif isinstance(error, exceptions.NotInRange):
            embed.description = _("The number `{0}` isn't allowed, it has to be in range {1}-{2}.") \
                .format(error.argument, error.min_int, error.max_int)
        elif isinstance(error, exceptions.NotInLength):
            embed.description = _("The text `{0}` isn't allowed, it has to be {1}-{2} characters long.") \
                .format(error.argument, error.min_len, error.max_len)
        elif isinstance(error, exceptions.NotBool):
            embed.description = _("The value `{0}` isn't allowed, it has to be on or off.") \
                .format(error.argument)
        elif isinstance(error, exceptions.NotLanguage):
            embed.description = _("The language `{0}` isn't a available language. Available languages: {1}") \
                .format(error.argument, ", ".join(error.available_languages))
        elif isinstance(error, exceptions.NotYoutubeUrl):
            embed.description = _("The url `{0}` isn't a valid YouTube url.").format(error.argument)
        elif isinstance(error, commands.BadUnionArgument):
            embed.description = _("The argument `{0}` in command `{1}` has to be one of these: {2}") \
                .format(error.param.name, ctx.message.content,
                        ", ".join([converter.__name__.lower() for converter in error.converters]))
        elif isinstance(error, commands.ConversionError) or isinstance(error, commands.BadArgument):
            embed.description = _("A wrong argument were passed into the command `{0}`.") \
                .format(ctx.message.content)
        elif isinstance(error, commands.CommandNotFound) or isinstance(error, commands.NotOwner):
            embed.description = _("The command `{0}` wasn't found. To get a list of command use `{1}`.") \
                .format(ctx.message.content, f"{ctx.prefix}help")
        elif isinstance(error, exceptions.NotGuildAdmin):
            embed.description = _("The command `{0}` can only be executed by admins.") \
                .format(ctx.message.content)
        elif isinstance(error, exceptions.NoVoice):
            embed.description = _("To use the command `{0}` you have to be in an voice channel (not afk). "
                                  "Also, the bot has to be disconnect from voice.") \
                .format(ctx.message.content)
        elif isinstance(error, exceptions.SpecificChannelOnly):
            embed.description = _("On this server commands can only be executed in channel {0}.") \
                .format(error.channel.mention)
        elif isinstance(error, commands.NoPrivateMessage):
            pass
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = _("The bot is missing permissions to execute commands, please grant: `{0}`") \
                .format(", ".join(error.missing_perms))
        elif isinstance(error, commands.CheckFailure):
            embed.description = _("You're lacking permission to execute command `{0}`.") \
                .format(ctx.message.content)
        else:
            embed.description = _("An unknown error occured on command `{0}`. We're going to fix that soon!") \
                .format(ctx.message.content)
            logging.error(error)
            self.sentry.capture_exception(error)

        if not isinstance(error, commands.BotMissingPermissions):
            await self.delete_command(ctx)
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

    @tasks.loop(minutes=15)
    async def update_songs_list(self):
        """Post all songs in database to pastebin and set url"""
        songs = self.get_all_songs()
        formatted_songs = ""

        for song in songs:
            formatted_songs += f"{song['anime']}   ‧   {song['title']}   ‧   {song['youtube_url']}\n"

        url = pbwrap.Pastebin(self.credentials["pastebin"]["api_key"]).create_paste(formatted_songs, 1, "Shiro Songlist", "1H")
        self.songs_list_url = url


shiro = Shiro()
shiro.run(shiro.credentials["discord"]["token"])
