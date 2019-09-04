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

import lavalink
import psycopg2
from discord.ext import commands


class Songs(commands.Cog):
    """Fetch or store songs in database and play them.

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
    ll_host: `str`
        Host of the lavalink server.
    ll_port: `str`
        Port the lavalink server is running on.
    ll_password: `str`
        Password to authentificate on the lavalink server.
    lavalink: `lavalink.Client`
        Lavalink client to play music with.

    """

    def __init__(self, bot):
        self.bot = bot
        self.database = self.bot.get_cog("database")
        self.ll_host = self.bot.get_config("lavalink", "host")
        self.ll_port = self.bot.get_config("lavalink", "port")
        self.ll_password = self.bot.get_config("lavalink", "password")
        self.lavalink = None
        self.init_lavalink()

        self.lavalink.add_event_hook(self.on_lavalink_event)
        self.bot.add_listener(self.lavalink.voice_update_handler, "on_socket_response")

    def cog_unload(self):
        """Clears event hooks from Lavalink.

        Currently there's no public member available for that.

        """
        self.lavalink._event_hooks.clear()

    def init_lavalink(self):
        """Establish connection to lavalink server.

        Lavalink is used to play songs and has to be setup.

        """
        credentials = {
            "host": self.ll_host,
            "port": self.ll_port,
            "password": self.ll_password,
            "region": "us"
        }
        self.lavalink = lavalink.Client(self.bot.user.id)
        self.lavalink.add_node(**credentials)

    async def on_lavalink_event(self, event):
        """Track events raised by lavalink.

        Parameters
        ----------
        event: :obj:`lavalink.events.Event`
            Event that was called.

        """
        events = (lavalink.events.QueueEndEvent, lavalink.events.TrackStuckEvent, lavalink.events.TrackExceptionEvent)
        if isinstance(event, events):
            await self.connect_voice(event.player.guild_id, None)

    async def connect_voice(self, guild_id, channel_id):
        """Connects to a voice channel, if None disconnects.

        Parameters
        ----------
        guild_id: :obj:`int`
            Guilds id where to join.
        channel_id: :obj:`int`
            Specific channel which should be joined.
            If `None` disconnects.

        """
        ws = self.bot._connection._get_websocket(guild_id)
        await ws.voice_state(guild_id, channel_id)

    def get_random_songs(self, category, amount):
        """Fetch a random amount of songs from the database.

        Parameters
        ----------
        category: :obj:`str`
            Can be `opening`, `ending`, `ost` or a custom guild id for the custom song quiz.
        amount: :obj:`int`
            The amount of songs to fetch from the database.

        Returns
        -------
        list
            List of songs that have been fetched.

        """
        sql = psycopg2.sql.SQL("SELECT * FROM songs WHERE category = %s ORDER BY RANDOM() LIMIT %s")
        return self.database.fetch(sql, [category, amount])


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Songs(bot))
