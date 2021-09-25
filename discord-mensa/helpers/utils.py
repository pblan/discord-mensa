import asyncio
from datetime import datetime, timedelta
import hikari
from hikari import Embed, Colour
from hikari.impl.special_endpoints import ActionRowBuilder
from hikari.interactions.base_interactions import PartialInteraction
import lightbulb
import requests
import uuid

from Constants import OPENMENSA_CANTEENS
from .formatting import INLINE_CODE

ON_DAY = lambda dt, day: dt + timedelta(days=(int(day) - dt.weekday()) % 7)


WEEKDAYS = [
    "Mo.",
    "Di.",
    "Mi.",
    "Do.",
    "Fr.",
    # "Sa.",
    # "So.",
]


async def create_menu_embed(
    ctx: lightbulb.context.Context, id: int, weekday: str
) -> Embed:
    target = ctx.get_guild().get_member(int(ctx.author))
    if not target:
        await ctx.respond("Der User ist nicht auf dem Server!")
        return

    date = ON_DAY(datetime.now(), weekday)

    response = requests.get(f"{OPENMENSA_CANTEENS}/{id}")

    assert response is not None  # function only gets called with valid a valid id

    response = response.json()
    mensa_name = response["name"]

    # check if mensa is closed
    response = requests.get(
        f"{OPENMENSA_CANTEENS}/{id}/days/{date.strftime('%Y-%m-%d')}"
    )

    try:
        response = response.json()

        # get meal plan
        response = requests.get(
            "{}/{}/days/{}/meals".format(
                OPENMENSA_CANTEENS, id, date.strftime("%Y-%m-%d")
            )
        )

        # print(f"{mensa_name}, Speiseplan vom {date.strftime('%d.%m.%Y')}")
        embed = (
            Embed(
                title=f"{mensa_name}, Speiseplan vom {date.strftime('%d.%m.%Y')}",
                description="",
                colour=Colour(0x00B1AB),
                timestamp=datetime.now().astimezone(),
            )
            .set_thumbnail(target.avatar_url)
            .set_footer(
                text="https://discord.paddel.xyz/mensabot", icon=ctx.member.avatar_url
            )
        )
        for meal in response.json():
            embed.add_field(
                name=meal["category"],
                value=f"{meal['name']}\n{INLINE_CODE(', '.join(set(meal['notes'])))}",
                inline=False,
            )
        return embed
    except:
        embed = Embed(
            title=f"{mensa_name}, Speiseplan vom {date.strftime('%d.%m.%Y')}",
            description="Geschlossen!",
            timestamp=datetime.now().astimezone(),
            color=0x00B1AB,
        )
        return embed


async def respond_menu(
    ctx: lightbulb.context.Context,
    id: int,
    weekday: int,
    interaction: PartialInteraction = None,
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

    uid = uuid.uuid4()

    for day in WEEKDAYS:
        buttons = (
            buttons.add_button(
                hikari.ButtonStyle.PRIMARY, f"{id}:{WEEKDAYS.index(day)}_{uid}"
            )
            .set_label(day)
            .set_is_disabled(False)
            .add_to_container()
        )

    if interaction is not None:
        await interaction.create_initial_response(
            hikari.ResponseType.MESSAGE_UPDATE, embed=embed, component=buttons
        )
    else:
        await ctx.respond(embed=embed, component=buttons)

    async with ctx.bot.stream(hikari.InteractionCreateEvent, 15.0).filter(
        lambda event: isinstance(event.interaction, hikari.ComponentInteraction)
        and str(uid) in event.interaction.custom_id
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
                # remember: f"{id}_{day}_{uid}"
                id = event.interaction.custom_id[
                    : event.interaction.custom_id.rindex(":")
                ]
                weekday = event.interaction.custom_id[
                    event.interaction.custom_id.rindex(":")
                    + 1 : event.interaction.custom_id.rindex("_")
                ]
                await event.interaction.create_initial_response(
                    hikari.ResponseType.MESSAGE_UPDATE,
                    embed=await create_menu_embed(
                        ctx,
                        int(id),
                        weekday,
                    ),
                )

    await ctx.edit_response(components=[])
    return
