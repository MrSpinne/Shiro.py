import discord
from discord.ext import commands

import json


class General(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        """Catch errors on command execution"""
        embed = discord.Embed(color=10892179, title="**Fehler bei Command**")

        if isinstance(error, commands.ConversionError) or isinstance(error, commands.BadArgument):
            embed.description = f"Beim Befehl `{ctx.message.content}` wurde ein falsches Argument angegeben. Für " \
                                "weiteres benutze `s.help`."
        elif isinstance(error, commands.MissingRequiredArgument):
            embed.description = f"Beim Befehl `{ctx.message.content}` fehlt das Argument `{error.param.name}`. Für " \
                                "weiteres benutze `s.help`."
        elif isinstance(error, commands.NoPrivateMessage):
            embed.description = f"Der Befehl `{ctx.message.content}` kann nur im Server ausgeführt werden. Für " \
                                "weiteres benutze `s.help`."
        elif isinstance(error, commands.CheckFailure):
            embed.description = f"Der Befehl `{ctx.message.content}` kann von dir hier nicht ausgeführt werden. " \
                                "Für weiteres benutze `s.help`."
        elif isinstance(error, commands.CommandNotFound):
            embed.description = f"Der Befehl `{ctx.message.content}` existiert nicht. Für weiteres benutze `s.help`."
        elif isinstance(error, commands.TooManyArguments):
            embed.description = f"Beim Befehl `{ctx.message.content}` wurden zu viele Argumente angegeben. Für " \
                                "weiteres benutze `s.help`."
        else:
            embed.description = f"Beim Befehl `{ctx.message.content}` ist ein unbekannter Fehler aufgetreten. " \
                                "Für weiteres benutze `s.help`."

        await ctx.send(embed=embed)
        embed.description = f"Der User {ctx.author.name}#{ctx.author.discriminator} hat einen Fehler " \
                            f"ausgelöst.\n`{ctx.message.content}` - `{error}`"
        await self.shiro.app_info.owner.send(embed=embed)

    @commands.command(brief="Übersicht für Commands")
    async def help(self, ctx):
        """Get information about other commands"""
        embed = discord.Embed(color=7830745, title="**Übersicht für Commands**", description="")
        for command in self.shiro.commands:
            embed.description += f"`s.{command.name} {command.usage if command.usage is not None else ''}` - {command.brief}\n"

        await ctx.send(embed=embed)

    @commands.command(brief="Information über Shiro")
    async def info(self, ctx):
        """Show bot author and amount of songs"""
        with open("data/songs.json", "r", encoding="utf8") as file:
            songs = json.load(file)

        embed = discord.Embed(color=7830745, title="**Information über Shiro**",
                              description=f"Shiro wurde von **{self.shiro.app_info.owner.name}#"
                                          f"{self.shiro.app_info.owner.discriminator}** in Python programmiert. Derzeit"
                                          f" gibt es **{len(songs)} Songs** in der Datenbank. Bei weiteren Fragen "
                                          "kannst du dich gerne melden!")
        embed.set_thumbnail(url=self.shiro.app_info.owner.avatar_url)
        await ctx.send(embed=embed)

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


def setup(shiro):
    shiro.add_cog(General(shiro))
