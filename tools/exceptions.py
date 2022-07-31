import discord


class GuildNotRegistered(discord.app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class GuildNotEnabled(discord.app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class MessageUnreachable(discord.app_commands.CheckFailure):
    def __init__(self):
        super().__init__()


class BadInput(discord.app_commands.CheckFailure):
    def __init__(self, message: str):
        self.message = message
        super().__init__(message)
