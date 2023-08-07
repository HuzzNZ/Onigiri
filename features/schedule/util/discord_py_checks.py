import discord
from discord import app_commands

from features.schedule.database import ScheduleDB
from features.schedule.exceptions import GuildNotRegistered, GuildNotEnabled


def guild_registered():
    async def predicate(interaction: discord.Interaction) -> bool:
        guild = await ScheduleDB().get_guild_exists(interaction.guild.id)
        if guild:
            return True
        else:
            raise GuildNotRegistered
    return app_commands.check(predicate)


def guild_enabled():
    async def predicate(interaction: discord.Interaction) -> bool:
        guild = await ScheduleDB().get_guild(interaction.guild.id)
        if guild.enabled:
            return True
        raise GuildNotEnabled
    return app_commands.check(predicate)


def author_is_editor():
    async def predicate(interaction: discord.Interaction) -> bool:
        db = ScheduleDB()
        guild = await db.get_guild(interaction.guild.id)
        for role_id in guild.editor_role_id_array:
            for role in interaction.user.roles:
                if role.id == role_id:
                    return True
        permissions = interaction.channel.permissions_for(interaction.user)
        return permissions.manage_guild
    return app_commands.check(predicate)


def author_is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        permissions = interaction.channel.permissions_for(interaction.user)
        return permissions.manage_guild
    return app_commands.check(predicate)
