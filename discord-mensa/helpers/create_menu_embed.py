import lightbulb
from hikari import Embed, Colour
from Constants import OPENMENSA_CANTEENS, INLINE_CODE, ON_DAY
from datetime import datetime, timedelta
import requests


async def create_menu_embed(
    ctx: lightbulb.context.Context, id: int, weekday: str
) -> Embed:
    target = ctx.get_guild().get_member(int(ctx.author))
    if not target:
        await ctx.respond("Der User ist nicht auf dem Server!")
        return

    date = ON_DAY(datetime.today(), weekday)

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
            # print(meal)
            embed.add_field(
                name=meal["category"],
                value=f"{meal['name']}\n{INLINE_CODE(', '.join(set(meal['notes'])))}",
                inline=False,
            )
    except:
        embed = Embed(
            title=f"{mensa_name}, Speiseplan vom {date.strftime('%d.%m.%Y')}",
            description="Geschlossen!",
            timestamp=datetime.now(),
            color=0x00B1AB,
        )
    return embed
