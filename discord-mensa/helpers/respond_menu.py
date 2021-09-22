import asyncio
import hikari
from hikari.impl.special_endpoints import ActionRowBuilder
from hikari.interactions.base_interactions import PartialInteraction
import lightbulb
import requests
import hikari

from Constants import OPENMENSA_CANTEENS, INLINE_CODE
from .create_menu_embed import create_menu_embed

WEEKDAYS = [
    "Mo.",
    "Di.",
    "Mi.",
    "Do.",
    "Fr.",
    # "Sa.",
    # "So.",
]


async def respond_menu(
    ctx: lightbulb.context.Context,
    id: int,
    weekday: int,
    interaction: PartialInteraction = None
    # edit_buttons: bool = False,
) -> None:
    target = ctx.get_guild().get_member(int(ctx.author))
    if not target:
        await ctx.respond("Der User ist nicht auf dem Server!")
        return

    response = requests.get("{}/{}".format(OPENMENSA_CANTEENS, id))

    try:
        response = response.json()
    except:
        await ctx.respond(
            f"Ich konnte keine Mensa mit der ID {INLINE_CODE(id)} finden. :("
        )
        return

    embed = await create_menu_embed(ctx, id, weekday)

    buttons = ActionRowBuilder()

    for day in WEEKDAYS:
        buttons = (
            buttons.add_button(hikari.ButtonStyle.PRIMARY, day)
            .set_label(day)
            .set_is_disabled(False)
            .add_to_container()
        )

    if interaction is not None:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_UPDATE, embed=embed, component=buttons
        )
        # await ctx.edit_response(
        #    embed=embed,
        #    component=buttons,
        #    # response_type=hikari.ResponseType.MESSAGE_UPDATE,
        # )
    else:
        await ctx.respond(embed=embed, component=buttons)

    try:
        event = await ctx.bot.wait_for(
            hikari.InteractionCreateEvent,
            predicate=(
                lambda event: isinstance(event.interaction, hikari.ComponentInteraction)
                and event.interaction.user.id == ctx.author.id
                and event.interaction.channel_id == ctx.channel_id
            ),
            timeout=15.0,
        )
        if event.interaction.custom_id in WEEKDAYS:
            # event.interaction.edit_initial_response(hikari.ResponseType.MESSAGE_UPDATE, None, )
            await respond_menu(
                ctx,
                id,
                WEEKDAYS.index(event.interaction.custom_id),
                interaction=event.interaction,
            )
    except asyncio.TimeoutError:
        await ctx.edit_response(components=[])  # component=None not working currently
        return
