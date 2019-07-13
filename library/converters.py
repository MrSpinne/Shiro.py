from discord.ext import commands
from library import exceptions

import pycountry
import requests
import re


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
        except:
            pass

        raise exceptions.NotInRange(argument, self.min_num, self.max_num)


class LengthStr(commands.Converter):
    """Converts to str if values length is in range"""
    def __init__(self, min_len, max_len):
        self.min_len = min_len
        self.max_len = max_len

    async def convert(self, ctx, argument):
        if self.min_len <= len(argument) <= self.max_len:
            return argument

        raise exceptions.NotInLength(argument, self.min_len, self.max_len)


class Bool(commands.Converter):
    """Converts to bool value if it's the specified"""
    def __init__(self, bool=None):
        self.bool = bool

    async def convert(self, ctx, argument):
        argument = argument.lower()
        if argument in ["true", "enable", "enabled", "on", "activate", "activated", "1"]:
            argument = True
        elif argument in ["false", "disable", "disabled", "off", "deactivate", "deactivated", "0"]:
            argument = False

        if (self.bool is None and isinstance(argument, bool)) or self.bool is argument:
            return argument

        raise exceptions.NotBool(argument, bool)


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
        available_languages = ctx.bot.get_languages()
        if argument in available_languages:
            return argument
        elif pycountry.languages.get(name=argument.capitalize()) is not None:
            return pycountry.languages.get(name=argument.capitalize()).alpha_2

        raise exceptions.NotLanguage(argument, available_languages)


class YoutubeUrl(commands.Converter):
    """Convert to youtube url if video is available"""
    async def convert(self, ctx, argument):
        try:
            requests.get(f"https://www.youtube.com/oembed?format=json&url={argument}").json()
            return argument
        except:
            raise exceptions.NotYoutubeUrl(argument)
