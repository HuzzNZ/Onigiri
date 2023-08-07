import logging

import discord
from discord.ext import commands

from api.database_api import OnigiriDB
from tools.constants import LOG_HANDLER

cogs = [
    "features.schedule.cog",
    "features.general.cog"
]


class Onigiri(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        self.db = OnigiriDB()
        self.logger = logging.getLogger("Onigiri")
        self.logger.setLevel(logging.INFO)
        self.logger.addHandler(LOG_HANDLER)
        self.ofs_auto_role_guild_id = 679651751753941002
        self.ofs_auto_role_role_id = 679653891595304985
        self.ofs_auto_role_status = self.db.get_auto_role_status(self.ofs_auto_role_guild_id)
        self.test_auto_role_status = self.db.get_auto_role_status(547571343986524180)
        super().__init__(command_prefix=commands.when_mentioned_or("$"), intents=intents)

    async def setup_hook(self):
        self.logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        for cog in cogs:
            await self.load_extension(cog)
            self.logger.info(f"Loaded cog {cog}!")

    async def on_member_join(self, member: discord.Member):
        self.logger.info(f'<{member.name} has joined {member.guild.name} ({member.guild.id}), '
                         f'pending = {member.pending}>')

    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.command:
            self.logger.info("")
            self.logger.info(
                f"<{interaction.user.name} used "
                f"/{interaction.command.qualified_name} in {interaction.guild.name} "
                f"({interaction.guild.id}).>")

    async def on_member_update(self, before: discord.Member, m: discord.Member):
        if not before.guild.id == self.ofs_auto_role_guild_id:
            return
        if self.ofs_auto_role_status and before.pending and not m.pending:
            self.logger.info(f'<{m.name} has been verified in {m.guild.name} ({m.guild.id}).>')
            await m.add_roles(self.get_guild(self.ofs_auto_role_guild_id).get_role(self.ofs_auto_role_role_id))
            self.logger.info("")
            self.logger.info(
                f"<User {m.id} ({m.name}) completed verification and was assigned a role in "
                f"{self.get_guild(self.ofs_auto_role_guild_id).name} ({self.ofs_auto_role_guild_id}).>"
            )
