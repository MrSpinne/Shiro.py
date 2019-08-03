#
#   SHIRO / Copyright MrSpinne / All rights reserved
#

import discord
from discord.ext import commands, tasks
from library import exceptions, checks, statposter

import psycopg2.extras
import psycopg2.sql
import pathlib
import inspect
import gettext
import builtins
import sentry_sdk.integrations.aiohttp
import logging
import dbl
import os
import lavalink
import Pymoe
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import configparser


class Shiro(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_prefix, case_insensitive=True, help_command=None, guild_subscriptions=False)
        builtins.__dict__["_"] = self.translate
        self.db_connector, self.db_cursor, self.app_info, self.gspread, self.credentials = None, None, None, None, {}
        self.sentry, self.lavalink, self.dbl, self.statposter, self.anilist = sentry_sdk, None, None, None, Pymoe.Anilist()
        self.parse_credentials()

    def parse_credentials(self):
        """Parse credentials from envs to file"""
        config = configparser.ConfigParser()
        config.read("config.ini")
        for section in config.sections():
            self.credentials[section.lower()] = {}
            for option in config.options(section):
                value = config.get(section, option)
                if value == "":
                    self.credentials[section.lower()][option] = os.environ.get("{0}_{1}".format(section, option))
                else:
                    self.credentials[section.lower()][option] = value

    async def on_ready(self):
        """Get ready and start"""
        logging.basicConfig(level=logging.INFO)
        self.connect_database()
        self.connect_lavalink()
        self.connect_optionals()

        self.update_guilds()
        self.load_all_extensions()
        self.add_command_handlers()
        self.app_info = await self.application_info()

        activity = discord.Activity(type=discord.ActivityType.playing, name="Song Quiz 🎵")
        await self.change_presence(activity=activity)
        logging.info(f"Ready to serve {len(self.users)} users in {len(self.guilds)} guilds")

    def connect_optionals(self):
        """Prepare start"""
        if self.credentials["sentry"].get("dsn"):
            self.sentry.init(**self.credentials["sentry"], integrations=[self.sentry.integrations.aiohttp.AioHttpIntegration()])
        if self.credentials["gspread"].get("type"):
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(self.credentials["gspread"], scope)
            self.gspread = gspread.authorize(credentials)
            self.update_songs_list.start()
        if self.credentials["botlist"].get("discordbots"):
            self.statposter = statposter.StatPoster(self)
            self.post_stats.start()

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
        except Exception as e:
            translation = string
            logging.error(e)
            self.sentry.capture_exception(e)

        return translation

    def connect_database(self):
        """Establish connection to postgres database"""
        self.db_connector = psycopg2.connect(**self.credentials["postgres"])
        self.db_cursor = self.db_connector.cursor(cursor_factory=psycopg2.extras.DictCursor)

    def disconnect_database(self):
        """Disconnect from database"""
        if self.db_connector:
            self.db_cursor.close()
            self.db_connector.close()

    def database_commit(self, sql, variables=None):
        """Commit data to database"""
        try:
            self.db_cursor.execute(sql, variables)
        except:
            self.db_connector.rollback()
        else:
            self.db_connector.commit()

    def database_fetch(self, sql, variables=None):
        """Fetch data from database"""
        try:
            self.db_cursor.execute(sql, variables)
        except:
            self.db_connector.rollback()
        else:
            return self.db_cursor.fetchall()

    def connect_lavalink(self):
        """Connect to lavalink server"""
        self.lavalink = lavalink.Client(self.user.id)
        self.lavalink.add_node(os.environ.get("LAVALINK_HOST"), os.environ.get("LAVALINK_PORT"),
                               os.environ.get("LAVALINK_PASSWORD"), os.environ.get("LAVALINK_REGION"))

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

    def register_guild(self, guild_id):
        """Register guild to database if it is not already registered"""
        sql = psycopg2.sql.SQL("INSERT INTO public.guilds (id) VALUES (%s) ON CONFLICT DO NOTHING")
        self.database_commit(sql, [guild_id])

    def unregister_guild(self, guild_id):
        """Unregister guild from database with all settings"""
        sql = psycopg2.sql.SQL("DELETE FROM public.guilds WHERE id = %s")
        self.database_commit(sql, [guild_id])

    def update_guilds(self):
        """Add or remove guilds from database to prevent bugs"""
        for guild in self.guilds:
            self.register_guild(guild.id)

        sql = psycopg2.sql.SQL("SELECT id FROM public.guilds")
        guild_ids = self.database_fetch(sql)
        for guild_id in guild_ids:
            if self.get_guild(guild_id["id"]) not in self.guilds:
                self.unregister_guild(guild_id["id"])

    def get_guild_setting(self, guild_id, setting):
        """Get guild setting from database"""
        sql = psycopg2.sql.SQL("SELECT {} FROM public.guilds WHERE id = %s").format(psycopg2.sql.Identifier(setting))
        return self.database_fetch(sql, [guild_id])[0][setting]

    def set_guild_setting(self, guild_id, setting, value):
        """Set guild setting in database to specified value"""
        sql = psycopg2.sql.SQL("UPDATE public.guilds SET {} = %s WHERE id = %s").format(psycopg2.sql.Identifier(setting))
        self.database_commit(sql, [value, guild_id])

    def get_random_songs(self, category, amount):
        """Get random songs from database"""
        sql = psycopg2.sql.SQL("SELECT * FROM public.songs WHERE category = %s ORDER BY RANDOM() LIMIT %s")
        return self.database_fetch(sql, [category, amount])

    def get_choice_songs(self, category, exclusion):
        """Get songs to fill quiz with"""
        sql = psycopg2.sql.SQL("SELECT * FROM public.songs WHERE category = %s AND url != %s ORDER BY RANDOM() LIMIT 4")
        return self.database_fetch(sql, [category, exclusion])

    def add_song(self, title, reference, url, category):
        """Add a song to the database"""
        sql = psycopg2.sql.SQL("INSERT INTO public.songs (title, reference, url, category) VALUES (%s, %s, %s, %s)")
        self.database_commit(sql, [title, reference, url, category])

    def get_song(self, song_id):
        """Get a song from database by id if exists"""
        sql = psycopg2.sql.SQL("SELECT * FROM public.songs WHERE id = %s")
        song = self.database_fetch(sql, [song_id])
        return song[0] if song else None

    def get_all_songs(self):
        """Get all songs from database in alphabetic order"""
        sql = psycopg2.sql.SQL("SELECT * FROM public.songs ORDER BY category, reference, title")
        return self.database_fetch(sql)

    def edit_song(self, song_id, setting, value):
        """Edit a song entry in database"""
        sql = psycopg2.sql.SQL("UPDATE public.songs SET {} = %s WHERE id = %s").format(psycopg2.sql.Identifier(setting))
        self.database_commit(sql, [value, song_id])

    async def delete_command(self, ctx):
        """Delete command if enabled in guild settings"""
        if ctx.guild is not None:
            if self.get_guild_setting(ctx.guild.id, "command_deletion") is True:
                try:
                    await ctx.message.delete()
                except discord.HTTPException:
                    pass

    async def on_message(self, message):
        """Send help if bot is mentioned"""
        if message.guild is None or message.author.bot:
            return

        if message.content.startswith(message.guild.me.mention):
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
        embed = discord.Embed(color=10892179, title=_("\\❌ **Error on command**"))
        if ctx.command:
            ctx.command.reset_cooldown(ctx)

        if isinstance(error, commands.MissingRequiredArgument):
            embed.description = _("The command `{0}` is missing the `{1}`.").format(
                ctx.message.content, error.param.name)
        elif isinstance(error, exceptions.NotInRange):
            embed.description = _("The number `{0}` isn't allowed, it has to be in range {1}-{2}.").format(
                error.argument, error.min_int, error.max_int)
        elif isinstance(error, exceptions.NotLengthStr):
            embed.description = _("The argument `{0}` is too long. Maximum allowed characters are {1}.").format(
                error.argument, error.max_len)
        elif isinstance(error, exceptions.NotPrefix):
            embed.description = _("The prefix `{0}` isn't allowed, it has to be 1-10 characters long and can only "
                                  "consist out of numbers and letters.").format(error.argument)
        elif isinstance(error, exceptions.NotBool):
            embed.description = _("The value `{0}` isn't allowed, it has to be on or off.").format(error.argument)
        elif isinstance(error, exceptions.NotLanguage):
            embed.description = _("The language `{0}` isn't a available language. Available languages: {1}").format(
                error.argument, ", ".join(error.available_languages))
        elif isinstance(error, exceptions.NotYoutubeURL):
            embed.description = _("The url `{0}` isn't a valid YouTube url or it's geo restricted.").format(error.argument)
        elif isinstance(error, exceptions.NotSongID):
            embed.description = _("The song id `{0}` isn't valid!").format(error.argument)
        elif isinstance(error, exceptions.NotCategory):
            embed.description = _("`{0}` isn't a valid song category.")
        elif isinstance(error, commands.BadUnionArgument):
            converter_names = ", ".join([converter.__name__.lower() for converter in error.converters])
            embed.description = _("The argument `{0}` in command `{1}` has to be one of these: {2}").format(
                error.param.name, ctx.message.content, converter_names)
        elif isinstance(error, (commands.ConversionError, commands.BadArgument)):
            embed.description = _("A wrong argument were passed into the command `{0}`.").format(ctx.message.content)
        elif isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, exceptions.NotTeam):
            embed.description = _("The command `{0}` can only be executed by team "
                                  "members on this server.").format(ctx.message.content)
        elif isinstance(error, commands.NotOwner):
            embed.description = _("The command `{0}` can only be executed by {1} on this server.")
        elif isinstance(error, exceptions.NotGuildAdmin):
            embed.description = _("The command `{0}` can only be executed by server admins.").format(ctx.message.content)
        elif isinstance(error, exceptions.NotVoted):
            embed.description = _("This command is only available for voters. Please [vote for free]({0}) "
                                  "to support this bot!").format("https://discordbots.org/bot/593116701281746955/vote")
        elif isinstance(error, exceptions.NoVoice):
            embed.description = _("To use the command `{0}` you have to be in an voice channel (not afk). "
                                  "Also, the bot can't serve multiple channels.").format(ctx.message.content)
        elif isinstance(error, exceptions.NoPlayer):
            embed.description = _("There's no playback to stop.")
        elif isinstance(error, exceptions.NotRequester):
            embed.description = _("Only the user who started the playback or an admin can stop it.")
        elif isinstance(error, exceptions.SpecificChannelOnly):
            embed.description = _("On this server commands can only be executed in channel {0}.").format(
                error.channel.mention)
        elif isinstance(error, commands.BotMissingPermissions):
            embed.description = _("The bot is missing permissions to execute commands, please grant: `{0}`").format(
                ", ".join(error.missing_perms))
        elif isinstance(error, commands.CheckFailure):
            embed.description = _("You're lacking permission to execute command `{0}`.").format(ctx.message.content)
        elif isinstance(error, commands.ExpectedClosingQuoteError):
            embed.description = _("You messed up quotation on `{0}`. If you use `\"`, you have to close it. If you "
                                  "want to use it as an input, escape it with `\\`.").format(ctx.message.content)
        elif isinstance(error, commands.InvalidEndOfQuotedStringError):
            embed.description = _("You messed up quotation on `{0}`. You have to separate the quoted arguments "
                                  "with spaces.").format(ctx.message.content)
        elif isinstance(error, commands.CommandOnCooldown):
            embed.description = _("Command on cooldown! Try again in {0} seconds.").format(int(error.retry_after))
        elif isinstance(error, commands.DisabledCommand):
            embed.description = _("All commands have been disabled because of a bot update. We'll be back in "
                                  "about 5 minutes. Please be patient.")
        else:
            embed.description = _("An unknown error occurred on command `{0}`. We're going to fix that soon!").format(
                ctx.message.content)
            logging.error(error)
            self.sentry.capture_exception(error)

        if not isinstance(error, commands.BotMissingPermissions):
            await self.delete_command(ctx)
            await ctx.send(embed=embed)
        elif (isinstance(error, commands.BotMissingPermissions) and "send_messages" not in error.missing_perms) or \
                (isinstance(error, commands.BotMissingPermissions) and "embed_links" not in error.missing_perms):
            await ctx.send(embed=embed)

    @tasks.loop(hours=1)
    async def update_songs_list(self):
        """Dump all songs in database to google sheet"""
        songs = self.get_all_songs()
        sheet = self.gspread.open("Shiro's Songs")
        formatted = []

        for song in songs:
            formatted.append([song["id"], song["title"], song["reference"], song["url"],
                              song["category"], song["updated"].strftime("%d. %B %Y - %H:%M:%S")])

        sheet.sheet1.resize(1)
        sheet.sheet1.resize(len(formatted) + 1)
        sheet.values_update("List!A2", params={"valueInputOption": "RAW"}, body={"values": formatted})

    @tasks.loop(minutes=15)
    async def post_stats(self):
        """Update status every 30 minutes"""
        try:
            await self.statposter.post_all(**self.credentials["botlist"])
        except Exception as e:
            self.sentry.capture_exception(e)
            # TODO: Specify exception


shiro = Shiro()
print(shiro.credentials["discord"]["token"])
shiro.run(shiro.credentials["discord"]["token"])
