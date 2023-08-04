from discord.app_commands import AppCommandError


class MessageUnreachable(AppCommandError):
    def __init__(self):
        self.message = "Messages were unable to be found. Please make sure the bot has correct permissions."
        super().__init__(self.message)
