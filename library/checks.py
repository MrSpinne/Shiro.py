from discord.ext import commands
from library import exceptions


def voice_available(ctx):
    """Checks if voice client and voice user is available"""
    if ctx.author.voice is None:
        raise exceptions.NoVoice

    if ctx.author.voice.afk:
        raise exceptions.NoVoice

    if ctx.voice_client is not None:
        raise exceptions.NoVoice

    if ["connect", "speak"] not in ctx.author.voice.channel.permission_for(ctx.bot.user):
        raise exceptions.NoVoice

    return True


def is_bot_owner(ctx):
    """Check if user is the bot owner"""
    if ctx.author != ctx.bot.app_info.owner:
        raise commands.NotOwner

    return True


def is_guild_owner(ctx):
    """Check if user is the guild owner"""
    if ctx.author != ctx.guild.owner:
        raise exceptions.NotGuildOwner

    return True


def guild_only(ctx):
    """Check if command sent in guild"""
    if ctx.guild is None:
        raise commands.NoPrivateMessage

    return True


def channel_only(ctx):
    """If enabled only allow command response in specified channel"""
    allowed_channel = ctx.bot.get_channel(ctx.bot.get_guild_setting(ctx.guild.id, "channel_only"))
    if ctx.channel != allowed_channel and allowed_channel is not None:
        raise exceptions.SpecificChannelOnly(allowed_channel)

    return True


def bot_has_permissions(ctx):
    """Check if the bot has all necessary permissions"""
    guild = ctx.guild
    me = guild.me if guild is not None else ctx.bot.user
    channel_permissions = ctx.channel.permissions_for(me)
    permissions = ["add_reactions", "read_messages", "send_messages", "manage_messages", "embed_links", "attach_files",
                   "read_message_history", "mention_everyone", "external_emojis"]

    missing = [permission for permission in permissions if getattr(channel_permissions, permission, None) is False]
    if missing:
        raise commands.BotMissingPermissions(missing)

    return True
