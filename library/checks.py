from discord.ext import commands
from library import exceptions


def voice_available(ctx):
    """Checks if voice client and voice user is available"""
    if ctx.author.voice is None:
        raise exceptions.NoVoice

    if ctx.author.voice.afk:
        raise exceptions.NoVoice

    player = ctx.bot.lavalink.players.get(ctx.guild.id)
    if player:
        raise exceptions.NoVoice

    channel_permissions = ctx.author.voice.channel.permissions_for(ctx.guild.me)
    permissions = ["connect", "speak"]
    missing = [permission for permission in permissions if getattr(channel_permissions, permission, None) is False]
    if missing:
        raise commands.BotMissingPermissions(missing)

    return True


def player_available(ctx):
    """Check if a player is registered on guild"""
    player = ctx.bot.lavalink.players.get(ctx.guild.id)
    if not player:
        raise exceptions.NoPlayer

    if not player.is_playing:
        raise exceptions.NoPlayer

    return True


def is_bot_owner(ctx):
    """Check if user is the bot owner"""
    if ctx.author != ctx.bot.app_info.owner:
        raise commands.NotOwner

    return True


def is_guild_admin(ctx):
    """Check if user is the guild owner"""
    if not getattr(ctx.author.guild_permissions, "administrator", None):
        raise exceptions.NotGuildAdmin

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
                   "read_message_history"]

    missing = [permission for permission in permissions if getattr(channel_permissions, permission, None) is False]
    if missing:
        raise commands.BotMissingPermissions(missing)

    return True


def is_user(ctx):
    """Check if user isn't a bot"""
    if ctx.author.bot:
        raise exceptions.NotUser

    return True


async def has_voted(ctx):
    """Check if the user has voted on dbl"""
    if not await ctx.bot.dbl.get_user_vote(ctx.author.id) and ctx.author.id != ctx.bot.app_info.owner.id:
        raise exceptions.NotVoted

    return True


def is_requester(ctx):
    """Check if a user has requested a song or is admin"""
    player = ctx.bot.lavalink.players.get(ctx.guild.id)
    if not getattr(ctx.author.guild_permissions, "administrator", None) and player.current.requester != ctx.author.id:
        raise exceptions.NotRequester

    return True
