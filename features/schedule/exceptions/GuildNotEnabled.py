from discord.app_commands import AppCommandError


class GuildNotEnabled(AppCommandError):
    def __init__(self):
        self.message = "This feature has been disabled on this server. Use:" \
                       "\n\n >  /schedule config enable\n\nto re-enable it."
        super().__init__(self.message)
