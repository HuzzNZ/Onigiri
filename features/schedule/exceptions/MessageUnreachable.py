from discord.app_commands import AppCommandError


class MessageUnreachable(AppCommandError):
    def __init__(self):
        self.message = "The schedule was unable to be found. Please make sure the bot has correct permissions, " \
                       "or run:\n\n >  /schedule setup"
        super().__init__(self.message)
