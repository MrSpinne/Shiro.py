"""
Shiro Discord Bot - A fun related anime bot
Copyright (C) 2019 MrSpinne

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime
import discord
from discord.ext import commands

from library import exceptions


def bot_has_permissions(**perms):
    """Check if the bot has the specified permisssions.

    If a voice permissions is passed, the bot will check the channel the user is in.

    Parameters
    ----------
    perms
        List of permissions to check for.

    Returns
    -------
    bool
        Only returns `True` if check passed.

    Raises
    ------
    exceptions.NotInVoice
        Raised when user is not in a voice channel but bot voice permissions are required.
    discord.ext.commands.BotMissingPermissions
        Raised when bot is missing a required permission.

    """
    def predicate(ctx):
        bot_user = ctx.guild.me if ctx.guild is not None else ctx.bot.user
        if isinstance(bot_user, discord.Member) and ctx.author.voice is not None:
            voice_perms = ctx.author.voice.channel.permissions_for(bot_user)
            for name, value in voice_perms:
                perms.pop(name, None)

        text_perms = ctx.channel.permissions_for(bot_user)
        for name, value in text_perms:
            perms.pop(name, None)

        if perms:
            raise commands.BotMissingPermissions(perms)

        return True

    return commands.check(predicate)


def is_guild_admin():
    """Check if a user has administrator in a guild permissions.


    Returns
    -------
    bool
        Only returns `True` if user is administrator passed.

    Raises
    ------
    exceptions.NotGuildAdmin
        Raised when user is not a guild administrator.

    """
    def predicate(ctx):
        text_perms = ctx.channel.permissions_for(ctx.author)
        if not getattr(text_perms, "administrator", None):
            raise exceptions.NotGuildAdmin

        return True

    return commands.check(predicate)


def has_voted():
    """Check if a user has voted on DiscordBots.org.

    This will be deactivated if no credentials are provided.

    Returns
    -------
    bool
        Only returns `True` if user has voted or the bot was restarted recently.

    Raises
    ------
    exceptions.NotVoted
        Raised when user has not voted.

    """
    def predicate(ctx):
        stats = ctx.bot.get_cog("stats")
        users = ctx.bot.get_cog("users")
        if not stats.dbl:
            return True
        if (datetime.now - stats.start_time).seconds / 3600 < 12:
            return True
        if users.get_user_info(ctx.author.id)["last_vote"].seconds / 3600 < 12:
            return True

        raise exceptions.NotVoted

    return commands.check(predicate)


def is_restricted_channel():
    """Check if the channel is the restricted one.

    If no channel is set, the check will always pass.

    Returns
    -------
    bool
        Only returns `True` if the channel is the correct one.

    Raises
    ------
    exceptions.NotRestrictedChannel
        Raised when a command is used in an prohibited channel.

    """
    def predicate(ctx):
        guilds = ctx.bot.get_cog("guilds")
        guild_config = guilds.get_guild_config(ctx.guild.id)
        channel = guild_config["restricted_channel"]
        if channel and channel != ctx.channel.id:
            raise exceptions.NotRestrictedChannel(channel)

        return True

    return commands.check(predicate)


def voice_available():
    """Check if bot is available to play music.

    This will return true if the bot is already in use.

    Returns
    -------
    bool
        Only returns `True` if the bot is available and the user in voice.

    Raises
    ------
    exceptions.NotInVoice
        Raised when the user is not in a voice channel or afk channel.
    exceptions.NoVoiceAvailable
        Raised when the bot is already playing.

    """
    def predicate(ctx):
        if not ctx.author.voice:
            raise exceptions.NotInVoice
        if ctx.author.voice.afk:
            raise exceptions.NotInVoice

        songs = ctx.bot.get_cog("songs")
        player = songs.lavalink.players.get(ctx.guild.id)
        if player.is_playing():
            channel = ctx.bot.get_channel(player.channel_id).mention
            raise exceptions.NoVoiceAvailable(channel)

        return True

    return commands.check(predicate)

# Old


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
    if ctx.author.id != ctx.bot.app_info.owner.id and 601376061418373141 not in role_ids and 601503055816687628 not in role_ids:
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


def has_voted(ctx):
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
