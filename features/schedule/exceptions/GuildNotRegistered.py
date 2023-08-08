from discord.app_commands import AppCommandError


class GuildNotRegistered(AppCommandError):
    def __init__(self):
        self.message = "This guild has not yet been set up. Use:\n\n >  /schedule setup\n\nfirst."
        super().__init__(self.message)
