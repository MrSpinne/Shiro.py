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
import ddblapi
import pbwrap
import os
import lavalink


class Shiro(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, case_insensitive=True, help_command=None)
        builtins.__dict__["_"] = self.translate
        self.credentials, self.db_connector, self.db_cursor, self.app_info = None, None, None, None
        self.sentry, self.songs_list_url, self.lavalink, self.dbl, self.ddbl = sentry_sdk, None, None, None, None
        self.startup()

    def startup(self):
        """Prepare start"""
        logging.basicConfig(level=logging.INFO)
        self.load_credentials()
        self.sentry.init(dsn=self.credentials["sentry"]["dsn"],
                         integrations=[self.sentry.integrations.aiohttp.AioHttpIntegration()])
        self.connect_database()
        self.add_command_handlers()
        self.update_songs_list.start()

    async def on_ready(self):
        """Get ready and start"""
        self.app_info = await self.application_info()
        self.update_guilds()
        self.connect_lavalink()
        self.dbl = dbl.Client(self, self.credentials["discordbots"]["api_key"])
        self.ddbl = ddblapi.DivineAPI(self.user.id, self.credentials["divinediscordbots"]["api_key"])
        self.load_all_extensions()
        self.update_status.start()
        logging.info(f"Ready to serve {len(self.users)} users in {len(self.guilds)} guilds")

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
        """Get credentials from file and overwrite them if environment variable is found"""
        with open("data/credentials.json", "r", encoding="utf-8") as file:
            credentials = json.load(file)

        for service, service_credentials in credentials.items():
            for credential in service_credentials.keys():
                if os.environ.get(f"{service}_{credential}") is not None:
                    credentials[service][credential] = os.environ[f"{service}_{credential}"]

        self.credentials = credentials

    def connect_database(self):
        """Establish connection to postgres database"""
        self.db_connector = psycopg2.connect(**self.credentials["postgres"])
        self.db_cursor = self.db_connector.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def disconnect_database(self):
        """Disconnect from database"""
        if self.db_connector:
            self.db_cursor.close()
            self.db_connector.close()

    def connect_lavalink(self):
        """Connect to lavalink server"""
        self.lavalink = lavalink.Client(self.user.id)
        self.lavalink.add_node(**self.credentials["lavalink"])

    def register_guild(self, guild_id):
        """Register guild to database if it is not already registered"""
        try:
            sql = psycopg2.sql.SQL("INSERT INTO public.guilds (id) VALUES (%s) ON CONFLICT DO NOTHING")
            self.db_cursor.execute(sql, [guild_id])
        except Exception as e:
            self.db_connector.rollback()
        else:
            self.db_connector.commit()

    def unregister_guild(self, guild_id):
        """Unregister guild from database with all settings"""
        try:
            sql = psycopg2.sql.SQL("DELETE FROM public.guilds WHERE id = %s")
            self.db_cursor.execute(sql, [guild_id])
        except Exception as e:
            self.db_connector.rollback()
        else:
            self.db_connector.commit()

    def update_guilds(self):
        """Add or remove guilds from database to prevent bugs"""
        for guild in self.guilds:
            self.register_guild(guild.id)

        try:
            sql = psycopg2.sql.SQL("SELECT id FROM public.guilds")
            self.db_cursor.execute(sql)
        except Exception as e:
            self.db_connector.rollback()
        else:
            for guild_id in self.db_cursor.fetchall():
                if self.get_guild(guild_id["id"]) not in self.guilds:
                    self.unregister_guild(guild_id["id"])

    def add_command_handlers(self):
        """Add global command checks and command invokes"""
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
        try:
            sql = psycopg2.sql.SQL("SELECT {} FROM public.guilds WHERE id = %s").format(psycopg2.sql.Identifier(setting))
            self.db_cursor.execute(sql, [guild_id])
        except:
            self.db_connector.rollback()
        else:
            return self.db_cursor.fetchone()[0]

    def set_guild_setting(self, guild_id, setting, value):
        """Set guild setting in database to specified value"""
        try:
            sql = psycopg2.sql.SQL("UPDATE public.guilds SET {} = %s WHERE id = %s").format(psycopg2.sql.Identifier(setting))
            self.db_cursor.execute(sql, [value, guild_id])
        except:
            self.db_connector.rollback() 
        else:
            self.db_connector.commit()

    def get_random_songs(self, category, amount):
        """Get random songs from database"""
        try:
            sql = psycopg2.sql.SQL("SELECT * FROM public.songs WHERE category = %s ORDER BY RANDOM() LIMIT %s")
            self.db_cursor.execute(sql, [category, amount])
        except:
            self.db_connector.rollback()
        else:
            return self.db_cursor.fetchall()

    def get_choice_songs(self, category, exclusion):
        try:
            sql = psycopg2.sql.SQL("SELECT * FROM public.songs WHERE category = %s AND url != %s ORDER BY RANDOM() LIMIT 4")
            self.db_cursor.execute(sql, [category, exclusion])
        except:
            self.db_connector.rollback()
        else:
            return self.db_cursor.fetchall()

    def get_all_songs(self):
        """Get all songs from database in alphabetic order"""
        try:
            sql = psycopg2.sql.SQL("SELECT * FROM public.songs ORDER BY reference")
            self.db_cursor.execute(sql)
        except:
            self.db_connector.rollback()
        else:
            return self.db_cursor.fetchall()

    def add_song(self, title, reference, url, category):
        """Add a song to the database"""
        try:
            sql = psycopg2.sql.SQL("INSERT INTO public.songs (title, reference, url, category) VALUES (%s, %s, %s, %s)")
            self.db_cursor.execute(sql, [title, reference, url, category])
        except:
            self.db_connector.rollback()
        else:
            self.db_connector.commit()

    def get_languages(self):
        """Get all languages found in locales"""
        languages = [item.name for item in pathlib.Path("locales").iterdir() if item.is_dir()]
        return languages

    async def delete_command(self, ctx):
        """Delete command if enabled in guild settings"""
        if ctx.guild is not None:
            if self.get_guild_setting(ctx.guild.id, "command_deletion") is True:
                try:
                    await ctx.message.delete()
                except:
                    pass

    async def on_message(self, message):
        """Send help if bot is mentioned"""
        if message.guild is None or message.author.bot:
            return

        if self.user in message.mentions:
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
            embed.description = _("The command `{0}` is missing the `{1}`.").format(
                ctx.message.content, error.param.name)
        elif isinstance(error, exceptions.NotInRange):
            embed.description = _("The number `{0}` isn't allowed, it has to be in range {1}-{2}.").format(
                error.argument, error.min_int, error.max_int)
        elif isinstance(error, exceptions.NotPrefix):
            embed.description = _("The prefix `{0}` isn't allowed, it has to be 1-10 characters long and can only "
                                  "consist out of numbers and letters.").format(error.argument)
        elif isinstance(error, exceptions.NotBool):
            embed.description = _("The value `{0}` isn't allowed, it has to be on or off.").format(error.argument)
        elif isinstance(error, exceptions.NotLanguage):
            embed.description = _("The language `{0}` isn't a available language. Available languages: {1}").format(
                error.argument, ", ".join(error.available_languages))
        elif isinstance(error, exceptions.NotYoutubeUrl):
            embed.description = _("The url `{0}` isn't a valid YouTube url or it's geo restricted.").format(error.argument)
        elif isinstance(error, commands.BadUnionArgument):
            converter_names = ", ".join([converter.__name__.lower() for converter in error.converters])
            embed.description = _("The argument `{0}` in command `{1}` has to be one of these: {2}").format(
                error.param.name, ctx.message.content, converter_names)
        elif isinstance(error, commands.ConversionError) or isinstance(error, commands.BadArgument):
            embed.description = _("A wrong argument were passed into the command `{0}`.").format(ctx.message.content)
        elif isinstance(error, commands.CommandNotFound) or isinstance(error, commands.NotOwner):
            embed.description = _("The command `{0}` wasn't found. To get a list of command use `{1}`.").format(
                ctx.message.content, f"{ctx.prefix}help")
        elif isinstance(error, exceptions.NotGuildAdmin):
            embed.description = _("The command `{0}` can only be executed by admins.").format(
                ctx.message.content)
        elif isinstance(error, exceptions.NoVoice):
            embed.description = _("To use the command `{0}` you have to be in an voice channel (not afk). "
                                  "Also, the bot can't serve multiple channels.").format(ctx.message.content)
        elif isinstance(error, exceptions.NotVoted):
            embed.description = _("This command is only available for voters. Please [vote for free]({0}) "
                                  "to support this bot!").format("https://discordbots.org/bot/593116701281746955/vote")
        elif isinstance(error, exceptions.NoPlayer):
            embed.description = _("There's no quiz to stop.")
        elif isinstance(error, exceptions.NotRequester):
            embed.description = _("Only the user who started the quiz or an admin can stop the playback.")
        elif isinstance(error, exceptions.SpecificChannelOnly):
            embed.description = _("On this server commands can only be executed in channel {0}.").format(
                error.channel.mention)
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = _("The bot is missing permissions to execute commands, please grant: `{0}`").format(
                ", ".join(error.missing_perms))
        elif isinstance(error, commands.CheckFailure):
            embed.description = _("You're lacking permission to execute command `{0}`.").format(ctx.message.content)
        else:
            embed.description = _("An unknown error occured on command `{0}`. We're going to fix that soon!").format(
                ctx.message.content)
            logging.error(error)
            self.sentry.capture_exception(error)

        if not isinstance(error, commands.BotMissingPermissions):
            await self.delete_command(ctx)
            await ctx.send(embed=embed)
        elif (isinstance(error, commands.BotMissingPermissions) and "send_messages" not in error.missing_perms) or \
                (isinstance(error, commands.BotMissingPermissions) and "embed_links" not in error.missing_perms):
            await ctx.send(embed=embed)

    @tasks.loop(minutes=30)
    async def update_status(self):
        """Update status every 5 minutes"""
        activity = discord.Activity(type=discord.ActivityType.playing, name="Song Quiz 🎵")
        await self.change_presence(activity=activity)
        await self.dbl.post_guild_count()
        await self.ddbl.post_stats(len(self.guilds))

    @tasks.loop(hours=3)
    async def update_songs_list(self):
        """Post all songs in database to pastebin and set url"""
        songs = self.get_all_songs()
        formatted_songs = ""

        for song in songs:
            formatted_songs += f"{song['title']} ∎ {song['reference']} ∎ {song['category']} ∎ {song['url']}\n"

        url = pbwrap.Pastebin(self.credentials["pastebin"]["api_key"]).create_paste(formatted_songs, 1, "Shiro Songlist", "1D")
        self.songs_list_url = url


shiro = Shiro()
shiro.run(shiro.credentials["discord"]["token"])
