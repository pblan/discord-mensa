import asyncio
from hikari import (
    Embed,
    CommandOption,
    OptionType,
    Colour,
    InteractionCreateEvent,
    ComponentInteraction,
)
from hikari.impl.special_endpoints import ActionRowBuilder

# from hikari.api.special_endpoints import ActionRowBuilder
import lightbulb
import typing
import requests
from geopy import Nominatim
from datetime import datetime

from Constants import OPENMENSA_CANTEENS, INLINE_CODE, GUILD_IDS

from ..helpers.respond_menu import respond_menu


class Mensa(lightbulb.slash_commands.SlashCommand):
    @property
    def options(self) -> list[CommandOption]:
        return [
            CommandOption(
                name="location",
                description="Wo befindet sich die Mensa?",
                type=OptionType.STRING,
                is_required=True,
            )
        ]

    @property
    def description(self) -> str:
        return "Gibt alle Mensen in einem Ort aus."

    @property
    def enabled_guilds(self) -> typing.Optional[typing.Iterable[int]]:
        return GUILD_IDS

    async def callback(self, ctx: lightbulb.context.Context) -> None:
        target = ctx.get_guild().get_member(int(ctx.author))
        if not target:
            await ctx.respond("Der User ist nicht auf dem Server!")
            return

        location = ctx.option_values.location or "Aachen"

        locator = Nominatim(user_agent="discord-mensa")
        found = locator.geocode(location)

        try:
            query = {
                "near[lat]": found.latitude,
                "near[lng]": found.longitude,
                "near[dist]": 5,
            }
        except:
            await ctx.respond(
                f"Ich konnte keinen Ort namens {INLINE_CODE(location)} finden!"
            )
            return

        response = requests.get(OPENMENSA_CANTEENS, params=query)

        # init embed message
        embed = (
            Embed(
                title=f"Mensen in der Nähe von {INLINE_CODE(location)}",
                description=f"Latitude = {found.latitude}, Longitude = {found.longitude}",
                colour=Colour(0x00B1AB),
                timestamp=datetime.now().astimezone(),
            )
            .set_thumbnail(target.avatar_url)
            .set_footer(
                text="https://discord.paddel.xyz/mensabot", icon=ctx.member.avatar_url
            )
        )

        # init select menu
        select_menu = (
            ActionRowBuilder()
            .add_select_menu("mensa_select")
            .set_placeholder("Wähle die Mensa aus...")
            .set_min_values(1)
            .set_max_values(1)
        )

        for mensa in response.json():
            # adding entries to the embed message
            embed.add_field(
                name=f"{mensa['name']}, ID: {mensa['id']}",
                value=f"{INLINE_CODE(mensa['address'])}",
                inline=False,
            )

            # adding entries to the select menu
            select_menu = (
                select_menu.add_option(  # add_option() returns a SelectOptionBuilder
                    f"{mensa['name']}, ID: {mensa['id']}", str(mensa["id"])
                )
                .set_description(f"{mensa['address']}")
                .add_to_menu()
            )

        await ctx.respond(
            embed=embed, component=select_menu.add_to_container()
        )  # add_to_container() returns the action row itself

        try:
            event = await ctx.bot.wait_for(
                InteractionCreateEvent,
                predicate=(
                    lambda event: isinstance(event.interaction, ComponentInteraction)
                    and event.interaction.user.id == ctx.author.id
                    and event.interaction.channel_id == ctx.channel_id
                ),
                timeout=15.0,
            )
            if event.interaction.custom_id == "mensa_select":
                # await ctx.edit_response(event.interaction.values, components=[])
                await respond_menu(
                    ctx,
                    event.interaction.values[0],
                    datetime.now().weekday(),
                    interaction=event.interaction,
                )
        except asyncio.TimeoutError:
            await ctx.edit_response(
                components=[]
            )  # component=None not working currently
            return
