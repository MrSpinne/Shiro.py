"""
Shiro Discord Bot - A fun related anime bot
Copyright (C) 2019 MrSpinne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import pathlib
import inspect
import gettext
import builtins
import logging
import os
import configparser
import signal
import sentry_sdk
import discord
from discord.ext import commands

from library import checks


class Shiro(commands.AutoShardedBot):
    """Main instance of the bot.

     Initialize everything and provide essential methods.

    """

    def __init__(self):
        super().__init__(command_prefix=commands.when_mentioned_or(self.get_prefix),
                         case_insensitive=True,
                         guild_subscriptions=False)
        builtins.__dict__["_"] = self.translate
        signal.signal(signal.SIGTERM, self.unload_all_extensions())

    def get_config(self, option, key):
        """Get the config for the bot.

        Enviromental variables will always be preferred.

        Parameters
        ----------
        option: :obj:`str`
            The option to look for.
            Similar to a section in `ConfigParser`.
        key: :obj:`str`
            The key to get from the option.

        Returns
        -------
        str
            Value assigned to the key of the option.

        """
        env = "{0}_{1}".format(option.upper(), key.upper())
        if os.environ.get(env):
            return os.environ.get(env)

        config = configparser.ConfigParser()
        config.read("data/config.ini")
        return config.get(option.capitalize(), key)

    def translate(self, string):
        """Translate string to language of ctx got from frame (commands only)"""
        language = "en"
        outer_frames = inspect.getouterframes(inspect.currentframe())
        for frame in outer_frames:
            arguments = inspect.getargvalues(frame.frame)
            if "ctx" in arguments.locals:
                if arguments.locals["ctx"].guild is not None:
                    guild_id = arguments.locals["ctx"].guild.id
                    guilds = self.get_cog("guilds")
                    language = guilds.get_guild_config(guild_id)["language"]
                    break

        try:
            translation = gettext.translation("base", "locales/", [language], codeset="utf-8").gettext(string)
        except FileNotFoundError as exception:
            translation = string
            logging.error(exception)
            sentry_sdk.capture_exception(exception)

        return translation

    def load_all_extensions(self):
        """Load all extensions from directory.

        These are located in `extensions/`.

        """
        extensions = [file.stem for file in pathlib.Path("extensions").glob("*.py")]
        for extension in extensions:
            self.load_extension(f"extensions.{extension}")

    def unload_all_extensions(self):
        """Unload all extensions which are currently loaded.

        Some extensions need to be unloaded to clear up connections.

        """
        for name, module_type in self.extensions:
            self.unload_extension(name)

    async def delete_invocation(self, ctx):
        """Delete the invocation message of a command.

        If no permissions are set or the message is not found this is silently ignored.

        """
        guilds = self.get_cog("guilds")
        if guilds.get_guild_config(ctx.guild.id)["restricted_channel"]:
            try:
                await ctx.message.delete()
            except discord.HTTPException:
                pass

    async def join_voice(self, ctx):
        """Join a voice channel if a command requires it.

        This is found out by looking for the regarding check.

        """
        songs = self.get_cog("songs")
        if checks.voice_available in ctx.commands.checks:
            songs.connect_voice(ctx.guild.id, ctx.author.voice.channel.id)

    async def get_prefix(self, message):
        """Return the prefix which the guild has set.

        This will wait until the bot is ready.

        """
        await self.wait_until_ready()
        if message.guild:
            guilds = self.get_cog("guilds")
            return guilds.get_guild_config(message.guild.id)["prefix"]

        return "s."

    async def on_ready(self):
        """Finish initializing by loading all extensions and adding command handlers.

        The presence of the bot will also be set.

        """
        self.load_all_extensions()
        self.add_check(commands.guild_only)
        self.add_check(checks.is_restricted_channel)
        self.before_invoke(self.delete_invocation)
        self.before_invoke(self.join_voice)
        activity = discord.Activity(type=discord.ActivityType.playing, name="Song Quiz 🎵")
        await self.change_presence(activity=activity)




    def get_choice_songs(self, category, exclusion):
        """Get songs to fill quiz with"""
        sql = psycopg2.sql.SQL("SELECT * FROM songs WHERE category = %s AND url != %s ORDER BY RANDOM() LIMIT 4")
        return self.database_fetch(sql, [category, exclusion])

    def add_song(self, title, reference, url, category):
        """Add a song to the database"""
        sql = psycopg2.sql.SQL("INSERT INTO songs (title, reference, url, category) VALUES (%s, %s, %s, %s)")
        self.database_commit(sql, [title, reference, url, category])

    def get_song(self, song_id):
        """Get a song from database by id if exists"""
        sql = psycopg2.sql.SQL("SELECT * FROM songs WHERE id = %s")
        song = self.database_fetch(sql, [song_id])
        return song[0] if song else None

    def get_all_songs(self):
        """Get all songs from database in alphabetic order"""
        sql = psycopg2.sql.SQL("SELECT * FROM songs ORDER BY category, reference, title")
        return self.database_fetch(sql)

    def edit_song(self, song_id, setting, value):
        """Edit a song entry in database"""
        sql = psycopg2.sql.SQL("UPDATE songs SET {} = %s WHERE id = %s").format(psycopg2.sql.Identifier(setting))
        self.database_commit(sql, [value, song_id])


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    SHIRO = Shiro()
    SHIRO.run(SHIRO.get_config("discord", "token"))
