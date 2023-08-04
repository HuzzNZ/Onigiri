from typing import List

from discord import app_commands


async def type_autocomplete(_, current: str) -> List[app_commands.Choice[str]]:
    """
    Autocomplete for event types.
    """
    types = ['stream', 'video', 'event', 'release', 'other']
    choices = []
    for t in types:
        if current.lower() in t:
            choices.append(app_commands.Choice(name=t, value=t))
    return choices
