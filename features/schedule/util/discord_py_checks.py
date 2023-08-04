import discord
from discord import app_commands


def guild_registered():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)


def author_is_editor():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)


def author_is_admin():
    def predicate(interaction: discord.Interaction) -> bool:
        return True  # TODO

    return app_commands.check(predicate)
