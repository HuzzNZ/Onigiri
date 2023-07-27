import discord
from discord import app_commands
from discord.ext.commands import Cog

from features.metadata import features
from onigiri import Onigiri

DESC_PREFIX = features['general']['desc_prefix']


class General(Cog):
    def __init__(self, client: Onigiri):
        self.client = client

    @app_commands.command(
        name="ping-new",  # TODO: Change in production
        description=DESC_PREFIX + "Pong!"
    )
    async def ping(self, interaction: discord.Interaction):
        # noinspection PyUnresolvedReferences
        await interaction.response.send_message(f"{interaction.user.mention} Pong!", ephemeral=True)


async def setup(client: Onigiri):
    await client.add_cog(General(client))
