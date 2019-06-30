import discord
from discord.ext import commands


class General(commands.Cog):
    def __init__(self, shiro):
        self.shiro = shiro

    @commands.command(brief="Übersicht für Commands")
    async def help(self, ctx):
        """Get information about other commands"""
        embed = discord.Embed(color=7830745, title="**Übersicht für Commands**", description="")
        for command in self.shiro.commands:
            embed.description += f"`s.{command.name} {command.usage if command.usage is not None else ''}` - {command.brief}\n"

        await ctx.send(embed=embed)

    @commands.command(brief="Information über Shiro")
    async def info(self, ctx):
        """Show bot author"""
        embed = discord.Embed(color=7830745, title="**Information über Shiro**",
                              description=f"Shiro wurde von **{self.shiro.app_info.owner.name}#"
                                          f"{self.shiro.app_info.owner.discriminator}** in Python programmiert.\nBei "
                                          "Fragen kannst du dich gerne melden!")
        embed.set_thumbnail(url=self.shiro.app_info.owner.avatar_url)
        await ctx.send(embed=embed)

    @commands.command(brief="Songanfrage stellen", usage="[Song]")
    async def request(self, ctx, song=None):
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
