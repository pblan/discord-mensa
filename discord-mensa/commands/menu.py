import hikari
import lightbulb
import typing
from datetime import datetime

from ..helpers.utils import respond_menu

from Constants import GUILD_IDS


class Menu(lightbulb.slash_commands.SlashCommand):
    # Options
    id: str = lightbulb.slash_commands.Option(
        description="ID der Mensa (siehe https://openmensa.org)", required=True
    )

    @property
    def description(self) -> str:
        return "Zeigt den Speiseplan einer Mensa an."

    @property
    def enabled_guilds(self) -> typing.Optional[typing.Iterable[int]]:
        return GUILD_IDS

    async def callback(self, ctx: lightbulb.context.Context) -> None:
        await respond_menu(ctx, ctx.option_values.id, datetime.today().weekday())
