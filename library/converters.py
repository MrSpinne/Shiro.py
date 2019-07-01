from discord.ext import commands


class RangeInt(commands.Converter):
    """Convert to int if number is in range"""
    def __init__(self, min_num, max_num):
        self.min_num = min_num
        self.max_num = max_num

    async def convert(self, ctx, argument):
        try:
            argument = int(argument)
            if argument in range(self.min_num, self.max_num+1):
                return argument
        except:
            pass

        raise commands.BadArgument(f"Argument {argument} not in range {self.min_num}-{self.max_num}.")
