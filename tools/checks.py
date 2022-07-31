import discord
from .exceptions import GuildNotRegistered


async def manage_messages(interaction: discord.Interaction) -> bool:
    guild = interaction.client.db.check_guild_exists(interaction.guild.id)
    if not guild:
        raise GuildNotRegistered
    try:
        guild_channel = interaction.client.get_channel(guild.get("schedule_channel_id"))
        perms = guild_channel.permissions_for(interaction.user).manage_messages
        if not perms:
            if guild.get("editor_role_id"):
                editor_role = interaction.guild.get_role(guild.get("editor_role_id"))
                perms = editor_role in interaction.user.roles
        return perms
    except discord.NotFound:
        return False


async def manage_channels(interaction: discord.Interaction) -> bool:
    return interaction.user.guild_permissions.manage_channels
