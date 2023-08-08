from discord.app_commands import AppCommandError


class InvalidArgument(AppCommandError):
    def __init__(self, message=""):
        super().__init__(message)
        self.message = message
