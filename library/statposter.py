import aiohttp
import json


class StatPoster:
    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=self.bot.loop, raise_for_status=True)

    async def discordbots(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://discordbots.org/api/bots/{self.bot.user.id}/stats"
        await self._post(url, data, headers)

    async def divinediscordbots(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://divinediscordbots.com/bot/{self.bot.user.id}/stats"
        await self._post(url, data, headers)

    async def discordbotreviews(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://discordbotreviews.xyz/api/bot/{self.bot.user.id}/stats"
        await self._post(url, data, headers)

    async def mythicalbots(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds)
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://mythicalbots.xyz/api/bot/{self.bot.user.id}"
        await self._post(url, data, headers)

    async def discordbotlist(self, token):
        data = json.dumps({
            "guilds": len(self.bot.guilds),
            "users": len(self.bot.users),
            "voice_connections": len(self.bot.lavalink.players)
        })
        headers = {
            "authorization": f"Bot {token}",
            "content-type": "application/json"
        }
        url = f"https://discordbotlist.com/api/bots/{self.bot.user.id}/stats"
        await self._post(url, data, headers)

    async def discordboats(self, token):
        data = json.dumps({
            "server_count": len(self.bot.guilds),
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://discord.boats/api/V2/bot/{self.bot.user.id}"
        await self._post(url, data, headers)

    async def botsondiscord(self, token):
        data = json.dumps({
            "guildCount": len(self.bot.guilds),
        })
        headers = {
            "authorization": token,
            "content-type": "application/json"
        }
        url = f"https://bots.ondiscord.xyz/bot-api/bots/{self.bot.user.id}/guilds"
        await self._post(url, data, headers)

    async def _post(self, url, data, headers):
        try:
            await self.session.post(url, data=data, headers=headers)
        except Exception as e:
            raise Exception(e)

    async def post_all(self, tokens):
        await self.discordbots(tokens["discordbots"])
        await self.divinediscordbots(tokens["divinediscordbots"])
        await self.discordbotreviews(tokens["discordbotreviews"])
        await self.mythicalbots(tokens["mythicalbots"])
        await self.discordbotlist(tokens["discordbotlist"])
        await self.discordboats(tokens["discordboats"])
        await self.botsondiscord(tokens["botsondiscord"])
