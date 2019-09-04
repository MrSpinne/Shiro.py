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

import copy
import psycopg2
from discord.ext import commands, tasks

from library import converters, checks


class Guilds(commands.Cog):
    """Add or remove guilds and let admins make changes to their per guild configuration.

    Parameters
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.

    Attributes
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.
    database: `discord.ext.commands.Cog`
        Database cog to use to commit or fetch data.
    default_config: ``
        Fallback config.

    """

    def __init__(self, bot):
        self.bot = bot
        self.database = self.bot.get_cog("database")
        self.default_config = {
            "prefix": "s.",
            "restricted_channel": None,
            "language": "en-US",
            "invocation_deletion": False
        }
        # TODO: Get default values from columns
        self.cleanup_guilds.start()

    @tasks.loop(hours=3.0)
    def cleanup_guilds(self):
        """Remove guilds from database the bot is not longer on.

        This is done to save disk space.

        """
        for guild_config in self.get_all_guild_configs():
            guild_id = guild_config["id"]
            guild_config = dict(guild_config)
            guild_config.pop("id")
            guild = self.bot.get_guild(guild_id)
            if guild_config == self.default_config:
                self.remove_guild(guild_id)
            elif guild not in self.bot.guilds:
                self.remove_guild(guild_id)

    def get_guild_config(self, guild_id):
        """Get guild and its configuration from database.

        Parameters
        ----------
        guild_id: obj:`int`
            Guilds id to fetch data from.

        Returns
        -------
        dict
            This has the fetched guild config.
            Returns default config if guild not in database.

        """
        sql = psycopg2.sql.SQL("SELECT * FROM guilds WHERE id = %s")
        try:
            guild_config = dict(self.database.fetch(sql, [guild_id])[0])
        except IndexError:
            guild_config = copy.deepcopy(self.default_config)
            guild_config["id"] = guild_id

        return guild_config

    def get_all_guild_configs(self):
        """Fetches all guilds from database.

        Returns
        -------
        list
            All guilds with config stored in `dict`s.

        """
        sql = psycopg2.sql.SQL("SELECT * FROM guilds")
        guild_configs = self.database.fetch(sql)
        return list(guild_configs)

    def set_guild_config(self, guild_id, option, value):
        """Changes an option of a guild.

        The guild will be added to database if not already present.

        Parameters
        ----------
        guild_id: :obj:`id`
            Guilds id to store in database or change config of.
        option: :obj:`str`
            The identifier of the option to change.
        value: :obj:`Any`
            The type is corresponding to the option.

        """
        sql = psycopg2.sql.SQL(
            "INSERT INTO guilds (id, {0}) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET ({0}) = (excluded.{0})"
        ).format(psycopg2.sql.Identifier(option))
        self.database.commit(sql, [guild_id, value])

    def remove_guild(self, guild_id):
        """Remove guild from database if present.

        Parameters
        ----------
        guild_id: :obj:`int`
            Guilds id to remove from database.

        """
        sql = psycopg2.sql.SQL("DELETE FROM guilds WHERE id = %s")
        self.database.commit(sql, [guild_id])

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        """Called if the bot was removed from a guild.

        If this happens remove guild also from database.

        Parameters
        ----------
        guild: :obj:`discord.Guild`
            Guild the bot removed from.

        """
        self.remove_guild(guild.id)

    @commands.command(aliases=["setprefix"], help=_("Change guild command prefix"))
    @checks.bot_has_permissions(send_messages=True)
    @checks.is_guild_admin()
    async def prefix(self, ctx, symbols: converters.Prefix):
        """Set the custom prefix per guild.

        Parameters
        ----------
        ctx: :obj:``
        symbols

        Returns
        -------

        """
        pass


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Guilds(bot))
