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

    """

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop)

    async def divinediscordbots(self, api_key):
        """Post stats to divinediscordbots.com.

        Posted stats: server count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://divinediscordbots.com/bot/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def discordbotreviews(self, api_key):
        """Post stats to discordbotreviews.xyz.

        Stats posted: server count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://discordbotreviews.xyz/api/bot/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def mythicalbots(self, api_key):
        """Post stats to mythical-bots.ml.

        Stats posted: server count

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": api_key,
            "content-type": "application/json"
        }
        url = f"https://mythicalbots.xyz/api/bot/{self.bot.user.id}"
        await self.post(url, data, headers)

    async def discordbotlist(self, api_key):
        """Post stats to discordbotlist.com.

        Stats posted: server count, user count, amount of voice connections

        Parameters
        ----------
        api_key: :obj:`str`
            Api key to post stats to bot page.

        """
        data = json.dumps({
            "guilds": len(self.bot.guilds),
            "users": len(self.bot.users),
            "voice_connections": len(self.bot.lavalink.players)
        })
        headers = {
            "authorization": f"Bot {api_key}",
            "content-type": "application/json"
        }
        url = f"https://discordbotlist.com/api/bots/{self.bot.user.id}/stats"
        await self.post(url, data, headers)

    async def discordboats(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds),
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://discord.boats/api/V2/bot/{self.bot.user.id}"
        await self.post(url, data, headers)

    async def botsondiscord(self, token):
        data = json.dumps({
            "guildCount": len(self.bot.guilds),
        })
        headers = {
            "authorization": token,
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
            A JSON formatted string with all data (like server count) to be sent.
        headers: :obj:`dict`
            All neccessary headers which are expected by the bot list.
            Bot lists will always require an `Authorization` header.

        """
        try:
            await self.session.post(url, data=data, headers=headers)
        except Exception:
            # FIXME: Catch specified exception and resolve status codes
            pass

    async def post_all(self, **kwargs):
        """Post the stats to the bot lists which have been configured.

        Parameters
        ----------
        divinediscordbots: :obj:`str`
            Api key for divinediscordbots.com to post stats to.
        discordbotreviews: :obj:`str`
            Api key for discordbotreviews.xyz to post stats to.
        mythicalbots: :obj:`str`
            Api key for mythical-bots.ml to post stats to.
        discordbotlist: :obj:`str`
            Api key for discordbotlist.com to post stats to.
        discordboats: :obj:`str`
            Api key for discord.boats to post stats to.
        botsondiscord: :obj:`str`
            Api key for bots.ondiscord.xyz to post stats to.

        """
        for bot_list, api_key in kwargs:
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
