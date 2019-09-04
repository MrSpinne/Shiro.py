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

import json
import aiohttp


class StatsPoster:
    """Post stats of the bot to the bot lists.

    Parameters
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.

    Attributes
    ----------
    bot: `discord.ext.commands.AutoShardedBot`
        Bot instance the cog was loaded into.
    session: `aiohttp.ClientSession`
        Session to use to perform http requests.
    api_keys: `dict`
        Api keys of the bot lists.
        Allowed bot lists can be looked up from the config.
    user_count: `int`
        Number of users the bot can see.
    guild_count: `int`
        Number of guilds the bot is on.
    voice_connections: `int`
        Number of players that are currently playing.

    """

    def __init__(self, bot, **api_keys):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)
        self.api_keys = api_keys
        self.user_count = None
        self.guild_count = None
        self.voice_connections = None
        self.update_stats()

    def update_stats(self):
        """Update the stats of the bot.

        Stats will be formatted stored as attributes.
        This also makes it possible to know which stats are currently displayed on bot lists.

        """
        self.user_count = len(self.bot.users)
        self.guild_count = len(self.bot.guilds)
        self.voice_connections = sum(player.is_playing is True for player in self.bot.lavalink.players)

    async def divinediscordbots(self, api_key):
        """Post stats to divinediscordbots.com.

        Posted stats: guild count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": self.guild_count
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://divinediscordbots.com/bot/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def discordbotreviews(self, api_key):
        """Post stats to discordbotreviews.xyz.

        Stats posted: guild count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": self.guild_count
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://discordbotreviews.xyz/api/bot/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def mythicalbots(self, api_key):
        """Post stats to mythical-bots.ml.

        Stats posted: guild count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": self.guild_count
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://mythicalbots.xyz/api/bot/{self.bot.user.id}"
        await self.post(url, data, headers)

    async def discordbotlist(self, api_key):
        """Post stats to discordbotlist.com.

        Stats posted: user count, guild count, amount of voice connections

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "users": self.user_count,
            "guilds": self.guild_count,
            "voice_connections": self.voice_connections
        })
        headers = {
            "authorization": f"Bot {api_key}",
            "content-type": "application/json"
        }
        url = f"https://discordbotlist.com/api/bots/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def discordboats(self, api_key):
        """Post stats to discord.boats.

        Posted stats: guild count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": self.guild_count,
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://discord.boats/api/V2/bot/{self.bot.user.id}"
        await self.post(url, data, headers)

    async def botsondiscord(self, api_key):
        """Post stats to bots.ondiscord.xyz.

        Posted stats: guild count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "guildCount": self.guild_count,
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.user.id}/guilds"
        await self.post(url, data, headers)

    async def post(self, url, data, headers):
        """Post data to specified url (bot list)

        This won't return a status code or raise an error.

        Parameters
        ----------
        url: :obj:`str`
            Url to send data to.
        data: :obj:`str`
            A JSON formatted string with all data (like guild count) to be sent.
        headers: :obj:`dict`
            All neccessary headers which are expected by the bot list.
            Bot lists will always require an `Authorization` header.

        """
        try:
            await self.session.post(url, data=data, headers=headers)
        except Exception:
            # FIXME: Catch specified exception and resolve status codes
            pass

    async def post_all(self):
        """Post the stats to the bot lists.

        Stats will only be posted to configured lists.

        """
        self.update_stats()
        for bot_list, api_key in self.api_keys:
            if api_key:
                if bot_list == "divinediscordbots":
                    await self.divinediscordbots(api_key)
                elif bot_list == "discordbotreviews":
                    await self.discordbotreviews(api_key)
                elif bot_list == "mythicalbots":
                    await self.mythicalbots(api_key)
                elif bot_list == "discordbotlist":
                    await self.discordbotlist(api_key)
                elif bot_list == "discordboats":
                    await self.discordboats(api_key)
                elif bot_list == "botsondiscord":
                    await self.botsondiscord(api_key)
