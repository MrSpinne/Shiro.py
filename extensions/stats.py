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
from datadog import initialize, statsd


class Stats(commands.Cog):
    """Post bot stats to Datadog and Discord bot lists.

    Parameters
    ----------
    bot: :obj:`discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.

    Attributes
    ----------
    bot: :obj:`discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.
    dd_api_key: :obj:`str`
        Datadog api key to post stats to.
    dd_app_key: :obj:`str`
        Datadog app key to post stats to.

    """

    def __init__(self, bot):
        self.bot = bot
        self.dd_api_key = self.bot.config["datadog"]["api_key"]
        self.dd_app_key = self.bot.config["datadog"]["app_key"]
        self.init_datadog()

    def init_datadog(self):
        """Initialize connection to Datadog to post metrics to and add event listener.

        This requires a Datadog api and app key to be set in the config.
        If no credentials are provided, Datadog won't be enabled.

        The `on_socket_response` event is called on any event.

        """
        if self.dd_api_key != "" and self.dd_app_key != "":
            initialize(self.dd_api_key, self.dd_app_key)
            self.bot.add_listener(self.track_events, "on_socket_response")

    async def track_events(self, payload):
        """
        Track every event and post the type to Datadog for analyzation purposes.

        Parameters
        ----------
        payload: :obj:`dict`
            Socket response with event type.

        Returns
        -------
        None

        """
        event = payload.get("t")
        statsd.increment(event)

    def init_bot_lists(self):
        """Initialize stats posting to the bot lists. This will also setup vote recognition.

        Only bot lists with credentials will be initialized.
        If DiscordBot credentials are not set then vote locking will be disabled.

        Returns
        -------
        None

        """
        pass


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`commands.AutoShardedBot`

    """
    bot.add_cog(Stats(bot))
