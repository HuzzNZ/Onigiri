from tools.constants import WARNING

dp = "〈Schedule〉"


class Descriptions:
    def __init__(self):
        self.title = "The title of the event. (Max: 30 characters)"

        self.optional_title = "The title of the event. (Max: 30 characters, Default: The title of the YouTube video)"

        self.event_id = "The 4 digit numerical ID of the event."

        self.event_type = "The type of the event. (Default: stream)"

        self.url = "An URL associated with an event."

        self.yt_url = "The YouTube URL associated with an event."

        self.note = "A note displayed under an event."

        self.date = "The date of the event in JST. (Example: Jul 12, 22/7/12, 7/12, 12 Jul 2022, " \
                    "October, 2023, today, tomorrow, etc.)"

        self.time = "The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.)"

        self.schedule_channel = "The channel to host the schedule messages."

        self.description = "The description of the schedule. Leave out to reset the description."

        self.talent = "The talent of the schedule. Leave out to reset the talent."

        self.editor_role = "Users with this role can edit the schedule."

        self.cmd_setup = dp + "Sets the schedule channel and creates a new set of schedule messages."

        self.cmd_add = dp + "Adds an event to the schedule."

        self.cmd_add_yt = dp + "Adds an event to the schedule from a YouTube URL."

        self.cmd_refresh = dp + "Manually refreshes the schedule."

        self.cmd_config = dp + "A set of commands to adjust the configurations for this server."

        self.cmd_config_status = dp + "Shows the configurations for this server."

        self.cmd_config_enable = dp + "Enables the schedule feature."

        self.cmd_config_disable = dp + "Disables the schedule feature."

        self.cmd_config_desc = dp + "Edits the description of the schedule. (Max: 200 characters)"

        self.cmd_config_talent = dp + "Edits the talent of the schedule. (Max: 30 characters)"

        self.cmd_config_editor_add = dp + "Adds a role to the schedule editor roles."

        self.cmd_config_editor_remove = dp + "Removes a role from the schedule editor roles. " \
                                             "Leave out to remove all roles."

        self.cmd_config_reset_all = dp + "Resets ALL schedule events, and configuration as if the bot was just added."

        self.cmd_config_reset_config = dp + "Resets configuration as if the bot was just added, but keeps all events."

        self.cmd_config_reset_events = dp + "Resets ALL schedule events, but keeps all configuration."

        self.cmd_edit = dp + "Edits an event. Only fields supplied will be edited."

        self.cmd_delete = dp + "Deletes an event."

        self.cmd_stash = dp + "Stashes an event."

        self.cmd_unstash = dp + "Unstashes an event."

        self.cmd_title = dp + "Sets the title of an event."

        self.cmd_date = dp + "Sets the date of an event. Leave out to remove."

        self.cmd_time = dp + "Sets the time of an event. Leave out to remove."

        self.cmd_url = dp + "Sets the URL of an event. Leave out to remove."

        self.cmd_note = dp + "Sets the note of an event. Leave out to remove."

        self.cmd_type = dp + "Sets the type of an event. Leave out to remove."

        self.cmd_history = dp + "Shows the history of schedule events on this server."


class Messages:
    def __init__(self):
        self.setup_override = f"{WARNING}**You are currently overriding the schedule channel.** This will create new " \
                              "schedule messages in {channel}, and render the current schedule messages static " \
                              "(can be safely deleted)."
