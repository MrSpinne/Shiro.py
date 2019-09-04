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

from discord.ext import commands
import psycopg2.extras
import psycopg2.sql


class Database(commands.Cog):
    """Handles database connections.

    Parameters
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.

    Attributes
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.
    pg_host: `str`
        Host postgres is running on.
    pg_port: `str`
        Port postgres is running on.
    pg_database: `str`
        Database in which tables are located (or should be created)
    pg_user: `str`
        User which should be used to execute sql.
    pg_password: `str`
        Password to login as the specified user.
    connector: `str`
        Established connection object. `None` if not connected.
    cursor: `str`
        Cursor to use. `None` if not connected.

    """

    def __init__(self, bot):
        self.bot = bot
        self.pg_host = self.bot.get_config("postgres", "host")
        self.pg_port = self.bot.get_config("postgres", "port")
        self.pg_database = self.bot.get_config("postgres", "database")
        self.pg_user = self.bot.get_config("postgres", "user")
        self.pg_password = self.bot.get_config("postgres", "password")

        self.connector = None
        self.cursor = None
        self.init_database()

    def cog_unload(self):
        """Disconnect from database to prevent bugs.

        Fired when the cog is unloaded.

        """
        if self.connector:
            self.cursor.close()
            self.connector.close()

    def init_database(self):
        """Initialize connection to postgres database.

        It will automatically create the `users`, `guilds` and `songs` table if not present.
        A sql schema is located at `data/schema.sql`.

        """
        credentials = {
            "host": self.pg_host,
            "port": self.pg_port,
            "database": self.pg_database,
            "user": self.pg_user,
            "password": self.pg_password
        }
        self.connector = psycopg2.connect(**credentials)
        self.cursor = self.connector.cursor(cursor_factory=psycopg2.extras.DictCursor)
        with open("data/schema.sql", "r") as file:
            data = file.read().replace("specify_user", self.pg_user)

        sql = psycopg2.sql.SQL(data)
        self.commit(sql)

    def commit(self, sql, variables=None):
        """Execute sql and commit changes to database.

        If an error occurs, no data will be committed and the action will be rollbacked.

        Parameters
        ----------
        sql: :obj:`psycopg2.sql.SQL`
            Sql query to execute and commit.
        variables: :obj:`list`
            List of variables to replace in sql. Can be `None`.

        """
        try:
            self.cursor.execute(sql, variables)
        except psycopg2.DatabaseError:
            self.connector.rollback()
        else:
            self.connector.commit()

    def fetch(self, sql, variables=None):
        """Fetch data from database by executing sql.

        Parameters
        ----------
        sql: :obj:`psycopg2.sql.SQL`
            Sql query to execute and fetch results from.
        variables: :obj:`list`
            List of variables to replace in sql. Can be `None`.

        Returns
        -------
        Optional[psycopg2.extras.OrderedDict]
            This has all fetched results and can be accessed with keys or indices.

        """
        try:
            self.cursor.execute(sql, variables)
        except psycopg2.DatabaseError:
            self.connector.rollback()
        else:
            return self.cursor.fetchall()


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Database(bot))
