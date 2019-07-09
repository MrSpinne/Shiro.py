import discord
from discord.ext import commands
from library import checks

import json


class General(commands.Cog):
	def __init__(self, shiro):
		self.shiro = shiro

	@commands.command()
	async def help(self, ctx):
		"""Get information about all commands"""
		embed = discord.Embed(color=7830745, title=_("**All commands**"),
		                      description=_(""))


		await ctx.send(embed=embed)

	@commands.command(brief="Information über Shiro")
	async def info(self, ctx):
		"""Show bot author and amount of songs"""
		with open("data/songs.json", "r", encoding="utf8") as file:
			songs = json.load(file)

		embed = discord.Embed(color=7830745, title=_("**Information über Shiro**"),
		                      description=f"Shiro wurde von **{self.shiro.app_info.owner.name}#"
		                                  f"{self.shiro.app_info.owner.discriminator}** in Python programmiert. Derzeit"
		                                  f" gibt es **{len(songs)} Songs** in der Datenbank. Bei weiteren Fragen "
		                                  "kannst du dich gerne melden!")
		embed.set_thumbnail(url=self.shiro.app_info.owner.avatar_url)
		await ctx.send(embed=embed)

	@commands.command(brief="Server-Einstellungen")
	@commands.check(checks.is_guild_owner)
	async def settings(self, ctx):
		"""Change the guild settings"""
		prefix = self.shiro.get_guild_setting(ctx.guild.id, "prefix")
		command_deletion = "aktiviert" if self.shiro.get_guild_setting(ctx.guild.id, "command_deletion") is True else "deaktiviert"
		channel_only = self.shiro.get_channel(self.shiro.get_guild_setting(ctx.guild.id, "channel_only"))
		channel_only = "deaktiviert" if channel_only is None else channel_only.mention
		language = self.shiro.get_guild_setting(ctx.guild.id, "language")
		embed = discord.Embed(color=7830745, title="**Server-Einstellungen**",
		                      description=f"\❕ Command Prefix ‧ `{prefix}`\n"
					                      f"\📝 Nachrichten löschen ‧ `{command_deletion}`\n"
		                                  f"\🔒 Nur ein Channel ‧ `{channel_only}`\n"
		                                  f"\🎌 Sprache ‧ `{language}`")
		message = await ctx.send(embed=embed)
		await message.add_reaction("❕")
		await message.add_reaction("📝")
		await message.add_reaction("🔒")
		await message.add_reaction("🎌")

	@commands.command(brief="Songanfrage stellen", usage="[Song]")
	async def request(self, ctx, *, song=None):
		"""Request a new song for the song quiz"""
		if song is None:
			embed = discord.Embed(color=7830745, title="**Songanfrage stellen**",
			                      description="Du hast ein neues Anime Opening/Ending, was wir ins Songquiz aufnehmen "
			                                  "sollen? Dafür muss der Song folgendes erfüllen:\n\n- Originalopening/"
			                                  "-ending\n- unverändert und in guter Qualität\n- von einem relevanten "
			                                  f"Anime\n\nNutze `s.request <anime - song - url>`")
			await ctx.send(embed=embed)
		else:
			embed = discord.Embed(color=7830745, title="**Songanfrage gestellt**",
			                      description="Deine Anfrage wurde erfolgreich eingereicht. Vielen Dank.")
			await ctx.send(embed=embed)
			embed = discord.Embed(color=7830745, title="**Neue Songanfrage**",
			                      description=f"Der Nutzer **{ctx.author.name}#{ctx.author.discriminator}** hat eine "
			                                  f"Anfrage gestellt. \nSong: `{song}`")
			await self.shiro.app_info.owner.send(embed=embed)

	@commands.command(brief="Bot stoppen")
	@commands.check(checks.is_bot_owner)
	async def shutdown(self, ctx):
		"""Stops the bot and closes connection"""
		embed = discord.Embed(color=7830745, title="**Bot stoppen**", description="Der Bot wird nun heruntergefahren.")
		await ctx.send(embed=embed)
		await self.shiro.shutdown()


def setup(shiro):
	shiro.add_cog(General(shiro))
