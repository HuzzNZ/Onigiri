import os
import traceback
from typing import Optional, Literal

import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy
from dotenv import load_dotenv

from onigiri import Onigiri
from tools.constants import *

load_dotenv()

if __name__ == "__main__":
    bot = Onigiri()
    tree = bot.tree


    @tree.error
    async def error_handler(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """
        The global error handler.
        """
        if hasattr(error, "message"):
            error_message = error.message
        elif isinstance(error, discord.app_commands.CheckFailure):
            error_message = "Missing permissions."
        else:
            bot.logger.exception(error)
            error_message = ''.join(traceback.TracebackException.from_exception(error).format())

        error_display = f"{NO}**Command `/{interaction.command.qualified_name}` failed**:\n```{error_message}```"
        try:
            # noinspection PyUnresolvedReferences
            await interaction.response.send_message(error_display, ephemeral=True)
        except discord.InteractionResponded:
            try:
                await interaction.edit_original_response(content=error_display)
            except discord.InteractionResponded:
                await interaction.followup.send(content=error_display, ephemeral=True)


    @bot.command()
    @commands.guild_only()
    async def auto_role_enable(ctx: Context):
        if not ctx.channel.permissions_for(ctx.author).manage_roles:
            return
        if ctx.guild.id not in [547571343986524180, 679651751753941002]:
            return
        elif ctx.guild.id == 547571343986524180:
            ctx.bot.test_auto_role_status = True
        elif ctx.guild.id == 679651751753941002:
            ctx.bot.ofs_auto_role_status = True
        ctx.bot.db.set_auto_role_status(ctx.guild.id, True)
        await ctx.send(f"{YES}**Enabled** auto-role upon user verification for **{ctx.guild.name}**.")


    @bot.command()
    @commands.guild_only()
    async def auto_role_disable(ctx: Context):
        if not ctx.channel.permissions_for(ctx.author).manage_roles:
            return
        if ctx.guild.id not in [547571343986524180, 679651751753941002]:
            return
        if ctx.guild.id == 547571343986524180:
            ctx.bot.test_auto_role_status = False
        else:
            ctx.bot.ofs_auto_role_status = False
        ctx.bot.db.set_auto_role_status(ctx.guild.id, False)
        await ctx.send(f"{YES}**Disabled** auto-role upon user verification for **{ctx.guild.name}**.")


    @bot.command()
    @commands.guild_only()
    async def auto_role_status(ctx: Context):
        if not ctx.channel.permissions_for(ctx.author).manage_roles:
            return
        if ctx.guild.id not in [547571343986524180, 679651751753941002]:
            return
        if ctx.guild.id == 547571343986524180:
            enabled_memory = ctx.bot.test_auto_role_status
        else:
            enabled_memory = ctx.bot.ofs_auto_role_status
        enabled_db = ctx.bot.db.get_auto_role_status(ctx.guild.id)
        ok = enabled_memory is enabled_db
        if ok:
            await ctx.send(
                f"Auto-role upon user verification for **{ctx.guild.name}** "
                f"is currently **{f'{YES}Enabled' if enabled_db else f'{NO}Disabled'}**."
            )
        else:
            await ctx.send(
                f"{WARNING} The status of auto-role upon user verification is **INCONSISTENT** "
                f"between database and memory. DB: **{f'{YES}Enabled' if enabled_db else f'{NO}Disabled'}**, "
                f"Memory: **{f'{YES}Enabled' if enabled_memory else f'{NO}Disabled'}**."
            )


    @bot.command()
    @commands.guild_only()
    @commands.is_owner()
    async def sync(
            ctx: Context,
            guilds: Greedy[discord.Object],
            spec: Optional[Literal["~", "*", "^"]] = None
    ) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands "
                f"{'globally' if spec is None else 'to the current guild.'}")
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

        await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")


    bot.run(os.getenv("WAKAME"))
