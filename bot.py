import os
import traceback
from typing import Optional, Literal

from dotenv import load_dotenv

import discord
from discord.ext import commands
from discord.ext.commands import Context, Greedy

from tools import *
from tools.constants import *
from onigiri import Onigiri

load_dotenv()


if __name__ == "__main__":
    bot = Onigiri()
    tree = bot.tree

    # @tree.command(description="Must be run at least once! "
    #                           "Sets up the bot, or edits schedule channel for the server.")
    # @app_commands.describe(channel="The channel to keep the schedule message in.")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @app_commands.check(manage_channels)
    # async def setup(interaction: discord.Interaction, channel: discord.TextChannel):
    #     await interaction.response.defer(ephemeral=True)
    #
    #     guild_id = interaction.guild.id
    #     schedule_channel_id = channel.id
    #
    #     current_guild = interaction.client.db.get_guild(guild_id)
    #
    #     if current_guild:  # Has this guild been set up yet?
    #         current_channel = current_guild.get("schedule_channel_id")
    #
    #         if current_channel == schedule_channel_id:  # Is the channel the same?
    #             migrated = bool(current_guild.get("schedule_message_ids"))
    #
    #             if migrated:  # Does the guild need migration to multiple messages?
    #                 current_messages = current_guild.get("schedule_message_ids")
    #                 if not current_messages:
    #                     current_messages = [current_guild.get("schedule_message_id")]
    #                 reset = False
    #                 try:
    #                     for m in current_messages:
    #                         channel = interaction.client.get_channel(current_channel)
    #                         await channel.fetch_message(m)
    #                 except (discord.NotFound, discord.Forbidden, AttributeError):
    #                     reset = True
    #
    #                 if not reset:  # Can the message be reached?
    #                     await interaction.followup.send(
    #                         f"{NO}**The schedule message channel is already "
    #                         f"<#{schedule_channel_id}>**."
    #                     )
    #                     return
    #     try:  # Try to make new messages
    #         messages = await interaction.client.new_schedule(guild_id, schedule_channel_id)
    #     except discord.Forbidden:
    #         await interaction.followup.send(
    #             f"{NO}**Setup failed.** Check that the bot has the permissions to **view**, "
    #             "and **send messages** in the correct channel."
    #         )
    #         return
    #     await interaction.client.update_schedule(guild_id)
    #     await interaction.followup.send(
    #         f"{YES}**The schedule message channel has been set to <#{schedule_channel_id}>**, "
    #         f"and new messages were created.\n> <{messages[0].jump_url}>")

    # @tree.command(description="Disables the bot on this server. (Does not remove event data!)")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @app_commands.check(manage_channels)
    # async def disable(interaction: discord.Interaction):
    #     guild = interaction.client.db.check_guild_exists(interaction.guild.id)
    #     if guild:
    #         result = interaction.client.db.disable_guild(interaction.guild.id)
    #         await interaction.response.send_message(
    #             f"{YES}**Bot disabled.** You can use **/enable** to enable me again!" if result else
    #             f"{NO}**Bot is already disabled.**", ephemeral=True
    #         )
    #     else:
    #         raise GuildNotRegistered
    #     await interaction.client.update_schedule(interaction.guild.id)
    #
    # @tree.command(description="Enables the bot on this server.")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @app_commands.check(manage_channels)
    # async def enable(interaction: discord.Interaction):
    #     guild = interaction.client.db.check_guild_exists(interaction.guild.id)
    #     if guild:
    #         result = interaction.client.db.enable_guild(interaction.guild.id)
    #         await interaction.response.send_message(
    #             f"{YES}**Bot enabled!** You can use **/disable** to disable me again." if result
    #             else f"{NO}**Bot is already enabled.**", ephemeral=True
    #         )
    #     else:
    #         raise GuildNotRegistered
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="set-editor", description="Sets a role that can access commands to edit the "
    #                                              "schedule.")
    # @app_commands.describe(editor="The role to set as an editor.")
    # @app_commands.rename(editor="role")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @check_general
    # @app_commands.check(manage_channels)
    # async def set_editor(interaction: discord.Interaction, editor: discord.Role = None):
    #     editor_id = editor.id if editor else None
    #     interaction.client.db.edit_guild_editor(interaction.guild.id, editor_id)
    #     await interaction.response.send_message(
    #         f"{YES}The schedule editor role has been set to **{editor.name}**." if editor else
    #         f"{YES}The schedule editor role has been **reset**.", ephemeral=True)

    # @tree.command(name="set-description", description="Sets a description for the schedule.")
    # @app_commands.describe(description="The description to set. Formatting will not work, but "
    #                                    "emojis will. (Max 200 characters)")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @check_general
    # @app_commands.check(manage_channels)
    # async def set_description(interaction: discord.Interaction, description: str = ""):
    #     if len(description) > 200:
    #         raise BadInput(
    #             f"**Description too long.** Max 200 characters. (Currently {len(description)})\n"
    #             "> **Tip:** *You can click on the **`... used /set-description`** "
    #             "on top of this message to retrieve your last command!*")
    #     interaction.client.db.edit_guild_description(interaction.guild.id, description)
    #     await interaction.response.send_message(
    #         f"{YES}**The description has been set.**" if description else
    #         f"{YES}**The description has been reset.**", ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)
    #
    # @tree.command(name="set-talent", description="Sets the name of the talent the schedule is for.")
    # @app_commands.describe(name="The name of talent that the schedule is for. (Max 30 characters)")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @check_general
    # @app_commands.check(manage_channels)
    # async def set_talent(interaction: discord.Interaction, name: str = ""):
    #     if len(name) > 30:
    #         raise BadInput(
    #             f"**Talent name too long.** Max 30 characters. (Currently {len(name)})\n"
    #             "> **Tip:** *You can click on the **`... used /set-talent`** "
    #             "on top of this message to retrieve your last command!*")
    #     interaction.client.db.edit_guild_talent(interaction.guild.id, name)
    #     await interaction.response.send_message(
    #         f"{YES}The talent has been set to **{name}**." if name else
    #         f"{YES}The talent has been **reset**.", ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="server-info", description="This server's configuration at a glance.")
    # @app_commands.guild_only()
    # @app_commands.default_permissions(manage_channels=True)
    # @check_general
    # @app_commands.check(manage_channels)
    # async def server_info(interaction: discord.Interaction):
    #     guild = interaction.client.db.get_guild(interaction.guild.id)
    #     editor_role_mention = f"<@&{guild.get('editor_role_id')}>" if guild.get('editor_role_id') \
    #         else "`None`"
    #     migrated = bool(guild.get('schedule_message_ids'))
    #     message_id_display = f'`{str(guild.get("schedule_message_id"))}`' if not migrated else \
    #         ', '.join([f'`{x}`' for x in guild.get('schedule_message_ids')])
    #     msg = f"__**{interaction.guild.name}'s {interaction.client.user.mention} " \
    #           f"Configuration**__\n\n" \
    #           f"> **Enabled**: {YES if guild.get('enabled') else NO}\n> \n" \
    #           f"> **Editor Role**: {editor_role_mention}\n> \n" \
    #           f"> **Talent Name**: {guild.get('talent', '`None`')}\n> \n" \
    #           f"> **Description**: {guild.get('description', '`None`')}\n> \n" \
    #           f"> **Schedule Channel**: <#{guild.get('schedule_channel_id')}>\n" \
    #           f"> **Schedule Message ID{'' if not migrated else 's'}**: " \
    #           f"{message_id_display}"
    #     await interaction.response.send_message(content=msg, ephemeral=True)

    # @app_commands.default_permissions(manage_channels=True)
    # class Reset(app_commands.Group):
    #     def __init__(self):
    #         super().__init__(description="Resets various things in the server.")
    #
    #     @app_commands.command(description="Resets all future events in this server.")
    #     @app_commands.guild_only()
    #     @app_commands.default_permissions(manage_channels=True)
    #     @check_general
    #     @app_commands.check(manage_channels)
    #     async def future(self, interaction: discord.Interaction):
    #         await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)
    #
    #     @app_commands.command(description="Resets all past events in this server.")
    #     @app_commands.guild_only()
    #     @app_commands.default_permissions(manage_channels=True)
    #     @check_general
    #     @app_commands.check(manage_channels)
    #     async def past(self, interaction: discord.Interaction):
    #         await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

    #     @app_commands.command(description="Resets all events in this server.")
    #     @app_commands.guild_only()
    #     @app_commands.default_permissions(manage_channels=True)
    #     @check_general
    #     @app_commands.check(manage_channels)
    #     async def events(self, interaction: discord.Interaction):
    #         await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)
    #
    #     @app_commands.command(description="Resets all configuration in this server.")
    #     @app_commands.guild_only()
    #     @app_commands.default_permissions(manage_channels=True)
    #     @check_general
    #     @app_commands.check(manage_channels)
    #     async def config(self, interaction: discord.Interaction):
    #         await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)
    #
    #     @app_commands.command(description="Resets all events, and configurations in this server.")
    #     @app_commands.guild_only()
    #     @app_commands.default_permissions(manage_channels=True)
    #     @check_general
    #     @app_commands.check(manage_channels)
    #     async def all(self, interaction: discord.Interaction):
    #         await interaction.response.send_message(f"{NO}**Not implemented yet!**", ephemeral=True)

    # @tree.command(description="Manually refreshes the schedule message.")
    # @app_commands.guild_only()
    # @check_general
    # @app_commands.check(manage_messages)
    # async def refresh(interaction: discord.Interaction):
    #     await interaction.response.defer(ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)
    #     await interaction.followup.send(content=f"{YES}**Schedule refreshed.**", ephemeral=True)

    # @tree.command(description="Pong!")
    # async def ping(interaction: discord.Interaction):
    #     await interaction.response.send_message(f"{interaction.user.mention} Pong!", ephemeral=True)

    # @tree.command(name="help", description="Links to the documentation page for the bot.")
    # async def help_command(interaction: discord.Interaction):
    #     await interaction.response.send_message(
    #         "**Check out the documentations here:**\n> "
    #         "<https://huzz.notion.site/Onigiri-Bot-Documentation-85760679057645aca767b94c867f3fd7>",
    #         ephemeral=True
    #     )

    # @tree.command(name='history', description="Shows the entire history of events.")
    # @app_commands.guild_only()
    # @check_general
    # async def history(interaction: discord.Interaction):
    #     guild = interaction.client.db.get_guild(interaction.guild.id)
    #     events = interaction.client.db.get_guild_events(interaction.guild.id)
    #     await interaction.response.send_message(
    #         embed=render_history(guild, events),
    #         ephemeral=True
    #     )

    # @tree.command(description="Adds an event to the schedule.")
    # @app_commands.describe(
    #     title="The title of the event. Max 30 characters. Try to keep it short and concise!",
    #     event_type="The type of the event. Defaults to stream.",
    #     url="The URL/Link of an event. YouTube stream/premiere URLs can be picked up.",
    #     date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, October, 2023"
    #          ", today, tomorrow, etc.)",
    #     time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.)")
    # @app_commands.guild_only()
    # @app_commands.autocomplete(event_type=type_ac)
    # @app_commands.rename(event_type="type")
    # @check_general
    # @check_date_time
    # @check_title
    # @check_url
    # @app_commands.check(manage_messages)
    # async def add(interaction: discord.Interaction,
    #               title: str, url: str = "", date: str = "", time: str = "",
    #               event_type: str = 'stream'):
    #     dt, dt_g = None, None
    #     if date:
    #         dt = parse_date(date)
    #         dt_g = parse_date(date, True)
    #         if time:
    #             dt = parse_time(time, dt)
    #     t = parse_type(event_type)
    #     event_id = interaction.client.db.add_event(interaction.guild_id, title, t, url, dt, dt_g)
    #     try:
    #         await interaction.response.send_message(f"{YES}**Event `{event_id}` added!**",
    #                                                 ephemeral=True)
    #     except discord.InteractionResponded:
    #         await interaction.edit_original_response(content=f"{YES}**Event `{event_id}` added!**")
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="add-yt", description="Adds an event to the schedule using a YouTube URL.")
    # @app_commands.describe(
    #     url="The YouTube URL linking to a video, premiere, or stream.",
    #     title="The title of the event. Max 30 characters. Defaults to the title of the YouTube "
    #           "video/stream.")
    # @app_commands.guild_only()
    # @check_general
    # @check_title
    # @check_url
    # @app_commands.check(manage_messages)
    # async def add_yt(interaction: discord.Interaction, url: str, title: str = None):
    #     try:
    #         await interaction.response.send_message(f"{NO}**No valid YouTube link found.**",
    #                                                 ephemeral=True)
    #     except discord.InteractionResponded:
    #         await interaction.edit_original_response(content=f"{NO}**Cancelled.**")
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(description="Deletes an event from the schedule.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.rename(event_id="id")
    # @app_commands.guild_only()
    # @check_general
    # @check_event_id
    # @app_commands.check(manage_messages)
    # async def delete(interaction: discord.Interaction, event_id: str):
    #     confirm = ConfirmView()
    #     await interaction.response.send_message(
    #         f"{WARNING}  **Are you sure you want to delete event `{event_id}`?**\n"
    #         f"> If the event was cancelled, consider using **/stash `{event_id}`**.",
    #         view=confirm, ephemeral=True)
    #     timeout = await confirm.wait()
    #     if not timeout:
    #         if confirm.value:
    #             interaction.client.db.delete_event(interaction.guild.id, event_id)
    #             await interaction.edit_original_response(
    #                 content=f"{YES}**Event `{event_id}` deleted.**", view=None
    #             )
    #             await interaction.client.update_schedule(interaction.guild.id)
    #         else:
    #             await interaction.edit_original_response(
    #                 content=f"{CANCELLED}  **Cancelled.**", view=None
    #             )
    #     else:
    #         await interaction.edit_original_response(
    #             content=f"{CANCELLED}  **Confirmation timed out.**", view=None
    #         )

    # @tree.command(description="Edits an event. Only edits the fields supplied.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(
    #     title="The title of the event. Max 30 characters. Try to keep it short and concise!",
    #     event_type="The type of the event. Defaults to stream.",
    #     url="The URL/Link of an event. YouTube stream/premiere URLs can be picked up.",
    #     date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, October, 2023"
    #          ", today, tomorrow, etc.)",
    #     time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, etc.)",
    #     note="The note to the event. Max 30 characters.")
    # @app_commands.rename(event_id="id")
    # @app_commands.rename(event_type="type")
    # @app_commands.guild_only()
    # @app_commands.autocomplete(event_type=type_ac)
    # @check_general
    # @check_event_id
    # @check_title
    # @check_url
    # @app_commands.check(manage_messages)
    # async def edit(interaction: discord.Interaction, event_id: str,
    #                title: str = None, url: str = "", date: str = "", time: str = "",
    #                event_type: str = 'stream', note: str = ''):
    #     if date:
    #         dt = parse_date(date)
    #         dt_g = parse_date(date, True)
    #         if time:
    #             dt = parse_time(time, dt)
    #         interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
    #         interaction.client.db.edit_event_datetime_granularity(
    #             interaction.guild.id, event_id, dt_g)
    #     elif time and not (date and time):
    #         date_dt = interaction.client.db.get_event(interaction.guild.id, event_id).get(
    #             "datetime"
    #         )
    #         dt = parse_time(time, date_dt)
    #         interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
    #     if title:
    #         interaction.client.db.edit_event_title(interaction.guild.id, event_id, title)
    #     if url:
    #         interaction.client.db.edit_event_url(interaction.guild.id, event_id, url)
    #     if event_type:
    #         interaction.client.db.edit_event_type(interaction.guild.id, event_id,
    #                                               parse_type(event_type))
    #     if note:
    #         if len(note) > 30:
    #             raise BadInput(
    #                 f"**Note too long.** Max 30 characters. (Currently {len(note)})\n"
    #                 f"> **Tip:** *You can click on the **`... used /edit`** "
    #                 f"on top of this message to retrieve your last command!*")
    #         interaction.client.db.edit_event_note(interaction.guild.id, event_id, note)
    #     try:
    #         await interaction.response.send_message(f"{YES}**Event `{event_id}` updated.**",
    #                                                 ephemeral=True)
    #     except discord.InteractionResponded:
    #         try:
    #             await interaction.edit_original_response(
    #                 content=f"{YES}**Event `{event_id}` updated.**")
    #         except discord.InteractionResponded:
    #             await interaction.followup.send(
    #                 content=f"{YES}**Event `{event_id}` updated.**", ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="title", description="Edits the title of an event.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(title="The title of the event. Max 30 characters.")
    # @app_commands.guild_only()
    # @app_commands.rename(event_id="id")
    # @check_general
    # @check_event_id
    # @check_title
    # @app_commands.check(manage_messages)
    # async def edit_title(interaction: discord.Interaction, event_id: str, title: str):
    #     interaction.client.db.edit_event_title(interaction.guild.id, event_id, title)
    #     await interaction.response.send_message(f"{YES}**Title of event `{event_id}` updated.**",
    #                                             ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="url", description="Edits the URL of an event. Enter nothing to reset the "
    #                                       "URL. Recognizes YouTube streams and premieres.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(url="The URL/Link of an event. YouTube stream/premiere URLs can be "
    #                            "picked up. Enter nothing to clear the URL.")
    # @app_commands.guild_only()
    # @app_commands.rename(event_id="id")
    # @check_general
    # @check_event_id
    # @check_url
    # @app_commands.check(manage_messages)
    # async def edit_url(interaction: discord.Interaction, event_id: str, url: str = ""):
    #     reset = False if url else True
    #     interaction.client.db.edit_event_url(interaction.guild.id, event_id, url)
    #     if reset:
    #         interaction.client.db.edit_event_confirmed(interaction.guild.id, event_id, False)
    #     try:
    #         await interaction.response.send_message(
    #             f"{YES}**URL of event `{event_id}` {'updated' if not reset else 'reset'}.**",
    #             ephemeral=True
    #         )
    #     except discord.InteractionResponded:
    #         await interaction.edit_original_response(
    #             content=f"{YES}**URL of event `{event_id}` {'updated' if not reset else 'reset'}.**"
    #         )
    #
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="date", description="Edits the date of an event. "
    #                                        "Editing the date will reset the time.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(
    #     date="The date of the event in JST. (e.g. Jul 12, 22/7/12, 7/12, 12 Jul 2022, October, 2023"
    #          ", today, tomorrow, etc.) Enter nothing clear the date.")
    # @app_commands.rename(event_id="id")
    # @app_commands.guild_only()
    # @check_general
    # @check_event_id
    # @check_date_time
    # @app_commands.check(manage_messages)
    # async def edit_date(interaction: discord.Interaction, event_id: str, date: str = ""):
    #     reset = False
    #     if date:
    #         dt = parse_date(date)
    #         dt_g = parse_date(date, True)
    #     else:
    #         dt = None
    #         dt_g = None
    #         reset = True
    #     interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
    #     interaction.client.db.edit_event_datetime_granularity(interaction.guild.id, event_id, dt_g)
    #     await interaction.response.send_message(
    #         f"{YES}**Date of event `{event_id}` {'updated' if not reset else 'reset'}.**",
    #         ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="time", description="Edits the time of an event. "
    #                                        "The event must already have a date.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(time="The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, "
    #                             "27:00, now, etc.), Enter nothing to clear the time.")
    # @app_commands.rename(event_id="id")
    # @app_commands.guild_only()
    # @check_general
    # @check_event_id
    # @check_date_time
    # @app_commands.check(manage_messages)
    # async def edit_time(interaction: discord.Interaction, event_id: str, time: str = ""):
    #     reset = False
    #     date_dt = interaction.client.db.get_event(interaction.guild.id, event_id).get("datetime")
    #     if time:
    #         dt = parse_time(time, date_dt)
    #     else:
    #         dt = parse_date(date_dt.strftime("%b %-d"))
    #         reset = True
    #     interaction.client.db.edit_event_datetime(interaction.guild.id, event_id, dt)
    #     await interaction.response.send_message(
    #         f"{YES}**Time of event `{event_id}` {'updated' if not reset else 'reset'}.**",
    #         ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(name="type", description="Edits the type of an event.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(event_type="The type of the event. Enter nothing to set to stream.")
    # @app_commands.rename(event_id="id")
    # @app_commands.guild_only()
    # @app_commands.autocomplete(event_type=type_ac)
    # @app_commands.rename(event_type="type")
    # @check_general
    # @check_event_id
    # @app_commands.check(manage_messages)
    # async def edit_type(interaction: discord.Interaction, event_id: str, event_type: str = ""):
    #     reset = False
    #     if not event_type:
    #         reset = True
    #         event_type = "stream"
    #     t = parse_type(event_type)
    #     interaction.client.db.edit_event_type(interaction.guild.id, event_id, t)
    #     await interaction.response.send_message(
    #         f"{YES}**Type of event `{event_id}` {'updated' if not reset else 'reset'}.**",
    #         ephemeral=True)
    #     await interaction.client.update_schedule(interaction.guild.id)

    # @tree.command(description="Stashes an event. An event will appear crossed out when stashed, "
    #                           "but it will not be deleted.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.rename(event_id="id")
    # @app_commands.guild_only()
    # @check_general
    # @check_event_id
    # @app_commands.check(manage_messages)
    # async def stash(interaction: discord.Interaction, event_id: str):
    #     event = interaction.client.db.get_event(interaction.guild.id, event_id)
    #     is_stashed = event.get("stashed", False)
    #     if not is_stashed:
    #         interaction.client.db.edit_event_stashed(interaction.guild.id, event_id, True)
    #         await interaction.response.send_message(
    #             f"{YES}**Event `{event_id}` stashed.**", ephemeral=True)
    #         await interaction.client.update_schedule(interaction.guild.id)
    #     else:
    #         await interaction.response.send_message(
    #             f"{NO}**Event `{event_id}` is already stashed!**", ephemeral=True)

    # @tree.command(description="Unstashes an event.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.guild_only()
    # @check_general
    # @check_event_id
    # @app_commands.check(manage_messages)
    # async def unstash(interaction: discord.Interaction, event_id: str):
    #     event = interaction.client.db.get_event(interaction.guild.id, event_id)
    #     is_stashed = event.get("stashed", False)
    #     if is_stashed:
    #         interaction.client.db.edit_event_stashed(interaction.guild.id, event_id, False)
    #         await interaction.response.send_message(
    #             f"{YES}**Event `{event_id}` unstashed.**", ephemeral=True)
    #         await interaction.client.update_schedule(interaction.guild.id)
    #     else:
    #         await interaction.response.send_message(
    #             f"{NO}**Event `{event_id}` is not stashed!**", ephemeral=True)

    # @tree.command(name="note", description="Edits the note to an event.")
    # @app_commands.describe(event_id=EVENT_ID_DESC)
    # @app_commands.describe(note="The note to the event. "
    #                             "Max 30 characters. Enter nothing to delete the note.")
    # @app_commands.guild_only()
    # @app_commands.rename(event_id="id")
    # @check_general
    # @check_event_id
    # @app_commands.check(manage_messages)
    # async def edit_note(interaction: discord.Interaction, event_id: str, note: str = ""):
    #     if len(note) > 30:
    #         raise BadInput(
    #             f"**Note too long.** Max 30 characters. (Currently {len(note)})\n"
    #             f"> **Tip:** *You can click on the **`... used /note`** "
    #             f"on top of this message to retrieve your last command!*",)
    #
    #     interaction.client.db.edit_event_note(interaction.guild.id, event_id, note)
    #     await interaction.response.send_message(
    #         f"{YES}**Note to event `{event_id}` updated.**" if note else
    #         f"{YES}**Note to event `{event_id}` deleted.**", ephemeral=True)
    #
    #     await interaction.client.update_schedule(interaction.guild.id)

    # tree.add_command(Reset())

    @tree.error
    async def error_handler(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """
        The global error handler.
        """

        if hasattr(error, "message"):
            error_message = error.message

        elif isinstance(error, GuildNotRegistered):
            error_message = "**This server has not yet been set up!** Run **/setup** first."

        elif isinstance(error, GuildNotEnabled):
            error_message = "**I'm currently disabled.** Run **/enable** to enable me."

        elif isinstance(error, MessageUnreachable):
            error_message = "**The schedule channel/message cannot be found.** Please check that the bot " \
                  "has permissions to **read**, and **send messages** in the correct channel. If " \
                  "the issue persists, try running **/setup** again."

        elif isinstance(error, BadInput):
            error_message = error.message

        elif isinstance(error, discord.app_commands.CheckFailure):
            error_message = "**Missing permissions.**"

        else:
            bot.logger.exception(error)
            error_message = ''.join(traceback.TracebackException.from_exception(error).format())

        error_display = f"{NO}**Command `/{interaction.command.qualified_name}` failed**:\n```{error_message}```"
        try:
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
