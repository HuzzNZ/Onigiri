from tools.constants import WARNING

dp = "〈Schedule〉"


class Descriptions:
    def __init__(self):
        self.title = "The title of the event. (Max: 30 characters)"

        self.event_type = "The type of the event. (Default: stream)"

        self.url = "An URL associated with an event."

        self.note = "A note displayed under an event."

        self.date = "The date of the event in JST. (Example: Jul 12, 22/7/12, 7/12, 12 Jul 2022, " \
                    "October, 2023, today, tomorrow, etc.)"

        self.time = "The time of the event in JST. (e.g. 8:00 pm, 20:00, 20, 3am, 27:00, now, etc.)"

        self.schedule_channel = "The channel to host the schedule messages."

        self.cmd_setup = dp + "First-time setup command. Sets the schedule channel and creates a new set of " \
                              "schedule messages."

        self.cmd_add = dp + "Adds an event to the schedule."


class Messages:
    def __init__(self):
        self.setup_override = f"{WARNING}**You are currently overriding the schedule channel.** This will create new " \
                              "schedule messages in {channel}, and render the current schedule messages static " \
                              "(can be safely deleted).",
