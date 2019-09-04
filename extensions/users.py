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
from datetime import datetime
import psycopg2
from discord.ext import commands, tasks


class Users(commands.Cog):
    """Store some users in database and fetch them.

    Only users who vote or team members will be stored.
    Otherwise the database would explode.

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
    stats: `discord.ext.commands.Cog`
        Stats cog to get data from.

    """

    def __init__(self, bot):
        self.bot = bot
        self.database = self.bot.get_cog("database")
        self.stats = self.bot.get_cog("stats")
        self.default_info = {"last_vote": 0}
        self.cleanup_users.start()

    @tasks.loop(hours=3.0)
    async def cleanup_users(self):
        """Remove users from database.

        Only users which have voted 12h ago will be deleted.

        """
        for user_info in self.get_all_user_infos():
            if (datetime.now() - user_info["last_vote"]).seconds / 3600 < 12:
                self.remove_user(user_info["id"])

    def set_user_info(self, user_id, option, value):
        """Register a users vote.

        Parameters
        ----------
        user_id: obj:`int`
            Id of the user to store vote in database.
        option: :obj:`str`
            The identifier of the option to change.
        value: :obj:`Any`
            The type is corresponding to the option.

        """
        sql = psycopg2.sql.SQL(
            "INSERT INTO users (id, {0}) VALUES (%s, %s) ON CONFLICT (id) DO UPDATE SET ({0}) = (excluded.{0})"
        ).format(psycopg2.sql.Identifier(option))
        self.database.commit(sql, [user_id, value])

    def get_user_info(self, user_id):
        """Get user info from database.

        Parameters
        ----------
        user_id: :obj:`int`
            Users id to fetch data from.

        Returns
        -------
        dict
            This has the user info.
            Returns default info if user not in database.

        """
        sql = psycopg2.sql.SQL("SELECT * FROM users WHERE id = %s")
        try:
            user_info = dict(self.database.fetch(sql, [user_id])[0])
        except IndexError:
            user_info = copy.deepcopy(self.default_info)
            user_info["id"] = user_id

        return user_info

    def get_all_user_infos(self):
        """Fetch all users from database.

        Returns
        -------
        list
            All users with info stored in `dict`s.

        """
        sql = psycopg2.sql.SQL("SELECT * FROM users")
        user_infos = self.database.fetch(sql)
        return list(user_infos)

    def remove_user(self, user_id):
        """Remove user from database if present.

        Parameters
        ----------
        user_id: :obj:`int`
            Users id to remove from database.

        """
        sql = psycopg2.sql.SQL("DELETE FROM users WHERE id = %s")
        self.database.commit(sql, [user_id])


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Users(bot))
