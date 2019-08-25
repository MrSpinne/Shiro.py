from discord.ext import commands
from library import exceptions

import pycountry
import re
import pathlib


class RangeInt(commands.Converter):
    """Convert to int if number is in range"""
    def __init__(self, min_num, max_num):
        self.min_num = min_num
        self.max_num = max_num

    async def convert(self, ctx, argument):
        try:
            argument = int(float(argument))
            if argument in range(self.min_num, self.max_num + 1):
                return argument
        except ValueError:
            pass

        raise exceptions.NotInRange(argument, self.min_num, self.max_num)


class LengthStr(commands.Converter):
    """Convert if str is not too long"""
    def __init__(self, max_len):
        self.max_len = max_len

    async def convert(self, ctx, argument):
        if len(argument) <= self.max_len:
            return argument

        raise exceptions.NotLengthStr(argument, self.max_len)


class Prefix(commands.Converter):
    """Converts to str if values length is in range"""
    async def convert(self, ctx, argument):
        if all(ord(c) < 128 for c in argument):
            return argument

        raise exceptions.NotPrefix(argument)


class Bool(commands.Converter):
    """Converts to bool value if it's the specified"""
    async def convert(self, ctx, argument):
        argument = argument.lower()
        if argument in ["true", "enable", "enabled", "on", "activate", "activated", "1"]:
            argument = True
        elif argument in ["false", "disable", "disabled", "off", "deactivate", "deactivated", "0"]:
            argument = False

        if isinstance(argument, bool):
            return argument

        raise exceptions.NotBool(argument)


class Nothing(commands.Converter):
    """Converts to None if value is meant to be nothing"""
    async def convert(self, ctx, argument):
        argument = argument.lower()
        if argument in ["none", "nil", "reset", "0", "empty"]:
            return None

        raise exceptions.NotNothing


class Language(commands.Converter):
    """Converts to language value if it's the specified"""
    async def convert(self, ctx, argument):
        argument = argument.lower()
        languages = [item.name for item in pathlib.Path("locales").iterdir() if item.is_dir()]

        for language in pycountry.languages:
            if getattr(language, "name", None) == argument.capitalize():

                if getattr(language, "alpha_2", None) in languages:
                    return language.alpha_2
            elif getattr(language, "alpha_2", None) == argument:
                if getattr(language, "alpha_2") in languages:
                    return language.alpha_2
            elif getattr(language, "alpha_3", None) == argument:
                if getattr(language, "alpha_2", None) in languages:
                    return language.alpha_2

        raise exceptions.NotLanguage(argument, languages)


class YoutubeURL(commands.Converter):
    """Convert to youtube url if video is available"""
    async def convert(self, ctx, argument):
        results = await ctx.bot.lavalink.get_tracks(argument)
        if results and results["tracks"]:
            video_id = re.search(r"((?<=([vV])/)|(?<=be/)|(?<=([?&])v=)|(?<=embed/))([\w-]+)", argument)[0]
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            return video_url

        raise exceptions.NotYoutubeURL(argument)


class Anime(commands.Converter):
    """Convert to anime"""
    async def convert(self, ctx, argument):
        search = ctx.bot.anilist.search.anime(argument, perpage=1)
        try:
            titles = search["data"]["Page"]["media"][0]["title"]
            anime = titles["english"] if titles["english"] is not None else titles["romaji"]
            return anime
        except KeyError:
            raise exceptions.NotAnime(argument)

        # TODO: Will be used in upcoming version


class SongID(commands.Converter):
    """Convert to song id if exits"""
    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
            if ctx.bot.get_song(argument):
                return argument
        except ValueError:
            pass

        raise exceptions.NotSongID(argument)


class Category(commands.Converter):
    """Convert to category if possible"""
    async def convert(self, ctx, argument):
        opening = ["op", "ops", "opening", "openings"]
        ending = ["ed", "eds", "ending", "endings"]
        ost = ["ost", "osts", "soundtrack", "soundtracks"]

        if argument.lower() in opening:
            return "Opening"
        if argument.lower() in ending:
            return "Ending"
        if argument.lower() in ost:
            return "OST"

        raise exceptions.NotCategory(argument)
