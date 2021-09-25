import asyncio
import hikari
from hikari import (
    Embed,
    CommandOption,
    OptionType,
    Colour,
    InteractionCreateEvent,
    ComponentInteraction,
)
from hikari.impl.special_endpoints import ActionRowBuilder
import lightbulb
import typing
import requests
from geopy import Nominatim
from datetime import datetime
import uuid

from ..helpers.utils import respond_menu
from ..helpers.formatting import INLINE_CODE
from Constants import OPENMENSA_CANTEENS, GUILD_IDS


class Mensa(lightbulb.slash_commands.SlashCommand):
    # Options
    location: str = lightbulb.slash_commands.Option(
        description="Wo befindet sich die Mensa?", required=True
    )

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
                # description=f"Latitude = {found.latitude}, Longitude = {found.longitude}",
                colour=Colour(0x00B1AB),
                timestamp=datetime.now().astimezone(),
            )
            .set_thumbnail(target.avatar_url)
            .set_footer(
                text="https://discord.paddel.xyz/mensabot", icon=ctx.member.avatar_url
            )
        )

        # init select menu
        custom_id = f"mensa_select{uuid.uuid1()}"
        select_menu = (
            ActionRowBuilder()
            .add_select_menu(custom_id)
            .set_placeholder("Wähle die Mensa aus...")
            .set_min_values(1)
            .set_max_values(1)
        )

        uid = uuid.uuid4()

        if len(response.json()) == 0:
            await ctx.respond(
                f"Ich konnte keine Mensen in der Nähe von {INLINE_CODE(location)} finden!"
            )
            return

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
                    f"{mensa['name']}, ID: {mensa['id']}", f"{str(mensa['id'])}_{uid}"
                )
                .set_description(f"{mensa['address']}")
                .add_to_menu()
            )

        await ctx.respond(
            embed=embed, component=select_menu.add_to_container()
        )  # add_to_container() returns the action row itself

        async with ctx.bot.stream(hikari.InteractionCreateEvent, 15.0).filter(
            lambda event: isinstance(event.interaction, hikari.ComponentInteraction)
            and str(uid) in event.interaction.values[0]
        ) as stream:
            async for event in stream:
                if (
                    event.interaction.user.id != ctx.author.id
                    or event.interaction.channel_id != ctx.channel_id
                ):
                    await event.interaction.create_initial_response(
                        hikari.ResponseType.MESSAGE_CREATE,
                        "Du kannst nicht mit dieser Nachricht interagieren!",
                        flags=hikari.MessageFlag.EPHEMERAL,
                    )
                else:
                    # that's dirty
                    # remember: f"{id}_{uid}"
                    id = event.interaction.values[0][
                        : event.interaction.values[0].rindex("_")
                    ]
                    await stream.close()
                    await respond_menu(
                        ctx,
                        int(id),
                        datetime.now().weekday(),
                        interaction=event.interaction,
                    )
                    return

        await ctx.edit_response(components=[])
        return
