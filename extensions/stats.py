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

from datetime import datetime
import dbl
from discord.ext import commands, tasks
from datadog import initialize, statsd

from library import statsposter


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
    users: `discord.ext.commands.Cog`
        Users cog to register votes to.
    start_time: `float`
        Time the bot was started.
    dd_api_key: :obj:`str`
        Datadog api key to post events to.
        Has to be set to activate Datadog.
    dd_app_key: :obj:`str`
        Datadog app key to post events to.
    statsposter: :obj:`statsposter.StatsPoster`
        Used to post bot stats to the bot lists but not DiscordBots.org.
        `None` if not initialized.
    dbl: :obj:`dbl.Client`
        DiscordBots client. This is `None` if no configuration found.
    dbl_api_key: :obj:`str`
        Api key for discordbots.org to post stats to.
    dbl_webhook_auth: :obj:`str`
        Webhook authorization for discordbots.org.
    dbl_webhook_path: :obj:`str`
        Path of the webhook to use for discordbots.org.
    dbl_webhook_port: :obj:`str`
        Port to use the webhook for discordbots.org on.
    bl_divinediscordbots: :obj:`str`
        Api key for divinediscordbots.com to post stats to.
    bl_discordbotreviews: :obj:`str`
        Api key for discordbotreviews.xyz to post stats to.
    bl_mythicalbots: :obj:`str`
        Api key for mythical-bots.ml to post stats to.
    bl_discordbotlist: :obj:`str`
        Api key for discordbotlist.com to post stats to.
    bl_discordboats: :obj:`str`
        Api key for discord.boats to post stats to.
    bl_botsondiscord: :obj:`str`
        Api key for bots.ondiscord.xyz to post stats to.

    """

    def __init__(self, bot):
        self.bot = bot
        self.users = self.bot.get_cog("users")
        self.start_time = datetime.now()
        self.dd_api_key = self.bot.get_config("datadog", "api_key")
        self.dd_app_key = self.bot.get_config("datadog", "app_key")
        self.statsposter = None

        self.dbl = None
        self.dbl_api_key = self.bot.get_config("discordbots", "api_key")
        self.dbl_webhook_auth = self.bot.get_config("discordbots", "webhook_auth")
        self.dbl_webhook_path = self.bot.get_config("discordbots", "webhook_path")
        self.dbl_webhook_port = self.bot.get_config("discordbots", "webhook_port")

        self.bl_divinediscordbots = self.bot.get_config("botlists", "divinediscordbots")
        self.bl_discordbotreviews = self.bot.get_config("botlists", "discordbotreviews")
        self.bl_mythicalbots = self.bot.get_config("botlists", "mythicalbots")
        self.bl_discordbotlist = self.bot.get_config("botlists", "discordbotlist")
        self.bl_discordboats = self.bot.get_config("botlists", "discordboats")
        self.bl_botsondiscord = self.bot.get_config("botlists", "botsondiscord")

        self.init_datadog()
        self.init_discordbots()
        self.init_statsposter()

    def init_datadog(self):
        """Initialize connection to Datadog to post metrics to and add event listener.

        This requires a Datadog api and app key to be set in the config.
        If no credentials are provided, Datadog won't be enabled.

        The `on_socket_response` event is called on any event.

        """
        if self.dd_api_key:
            initialize(self.dd_api_key, self.dd_app_key)

    @commands.Cog.listener()
    async def on_socket_response(self, payload):
        """
        Track every event and post the type to Datadog for analyzation purposes if configured.

        Parameters
        ----------
        payload: :obj:`dict`
            Socket response with event type.

        """
        if self.dd_api_key:
            event = payload.get("t")
            statsd.increment(event)

    def init_discordbots(self):
        """Initialize stats posting to the bot lists and vote recognition.

        This also registers a webhook to track votes.
        If DiscordBot credentials are not set, then it will be disabled.

        """
        if self.dbl_api_key:
            credentials = {
                "token": self.dbl_api_key,
                "bot": self.bot,
                "autopost": True,
                "webhook_auth": self.dbl_webhook_auth,
                "webhook_path": self.dbl_webhook_path,
                "webhook_port": self.dbl_webhook_port
            }
            self.dbl = dbl.Client(**credentials)

    @commands.Cog.listener()
    async def on_dbl_vote(self, data):
        """Track votes from DiscordBots.org and save it to database.

        This is automatically called by the event handler.

        Parameters
        ----------
        data: :obj:`dict`
            Data with vote info.

        """
        self.users.set_user_info(data.get("user"), "last_vote", datetime.now())

    def init_statsposter(self):
        """Initizialize the stats poster.

        Not configured bot lists won't receive stats.

        """
        credentials = {
            "divinediscordbots": self.bl_divinediscordbots,
            "discordbotreviews": self.bl_discordbotreviews,
            "mythicalbots": self.bl_mythicalbots,
            "discordbotlist": self.bl_discordbotlist,
            "discordboats": self.bl_discordboats,
            "botsondiscord": self.bl_botsondiscord
        }
        self.statsposter = statsposter.StatsPoster(self.bot, **credentials)
        self.post_bot_lists.start()

    @tasks.loop(minutes=30.0)
    async def post_bot_lists(self):
        """Post bot stats to the bot lists which have been configured.

        Currently available lists can be looked up from the config or the class attributes.

        """
        await self.statsposter.post_all()


def setup(bot):
    """Load the cog into the bot instance.

    Parameters
    ----------
    bot: :class:`discord.ext.commands.AutoShardedBot`

    """
    bot.add_cog(Stats(bot))
