from discord.app_commands import AppCommandError


class MessageUnsendable(AppCommandError):
    def __init__(self):
        self.message = "Message(s) were unable to be sent. Please make sure the bot has correct permissions."
        super().__init__(self.message)
