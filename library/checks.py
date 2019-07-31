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

    return True


def is_guild_admin(ctx):
    """Check if user is the guild owner"""
    if not getattr(ctx.author.guild_permissions, "administrator", None):
        raise exceptions.NotGuildAdmin

    return True


def is_team(ctx):
    """Check if user is team member of bot"""
    if ctx.guild.id != 600761022089003021:
        raise commands.CommandNotFound

    role_ids = [role.id for role in ctx.author.roles]
    if ctx.author != ctx.bot.app_info.owner and (601376061418373141 not in role_ids or 601503055816687628 not in role_ids):
        raise exceptions.NotTeam

    return True


def is_owner(ctx):
    """Check if user is owner of bot"""
    if ctx.guild.id != 600761022089003021:
        raise commands.CommandNotFound

    if ctx.author != ctx.bot.app_info.owner:
        raise commands.NotOwner

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
    permissions = ["add_reactions", "read_messages", "send_messages",
                   "manage_messages", "embed_links", "read_message_history"]

    missing = [permission for permission in permissions if getattr(channel_permissions, permission, None) is False]
    if missing:
        raise commands.BotMissingPermissions(missing)

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
