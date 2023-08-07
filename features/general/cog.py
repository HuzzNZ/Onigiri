import discord
from discord import app_commands
from discord.ext.commands import Cog

from features.metadata import features
from onigiri import Onigiri

DESC_PREFIX = features['general']['desc_prefix']


class General(Cog):
    def __init__(self, client: Onigiri):
        self.client = client

    @app_commands.command(name="ping", description=DESC_PREFIX + "Pong!")
    async def ping(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{interaction.user.mention} Pong!", ephemeral=True)

    @app_commands.command(name="help", description=DESC_PREFIX + "Links to the bot's documentation page.")
    async def help_command(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(
            "Check out the **[documentations]"
            "(https://huzz.notion.site/Onigiri-Bot-Documentation-85760679057645aca767b94c867f3fd7)**!\n ",
            ephemeral=True
        )


async def setup(client: Onigiri):
    await client.add_cog(General(client))
