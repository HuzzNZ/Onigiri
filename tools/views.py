import discord
from discord.ui import View, Button, button


class ConfirmView(View):
    def __init__(self):
        super().__init__(timeout=60)
        self.value = None

    @button(label='Confirm', style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, b: Button):
        self.value = True
        self.stop()

    @button(label='Cancel', style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, b: Button):
        self.value = False
        self.stop()


class PopulateFromURLView(View):
    def __init__(self):
        super().__init__(timeout=300)
        self.value = None

    @button(label='Use all', style=discord.ButtonStyle.blurple)
    async def replace_all(self, interaction: discord.Interaction, b: Button):
        self.value = True
        self.stop()

    @button(label="Don't use", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, b: Button):
        self.value = False
        self.stop()
