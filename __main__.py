from Constants import *

import os
from importlib import import_module
from pathlib import Path

import hikari
import lightbulb
import logging


def create_bot() -> lightbulb.Bot:

    bot = lightbulb.Bot(
        token=DISCORD_BOT_TOKEN,
        intents=hikari.Intents.ALL,
        slash_commands_only=True,
        # logs={
        #    "version": 1,
        #   "incremental": True,
        #   "loggers": {
        #       "hikari": {"level": "DEBUG"},
        #       "hikari.ratelimits": {"level": "TRACE_HIKARI"},
        #       "lightbulb": {"level": "DEBUG"},
        #    },
        # },
    )

    commands = Path("./discord-mensa/commands").glob("*.py")
    for c in commands:
        print(f"Loaded: {c}")
        mod = import_module(f"discord-mensa.commands.{c.stem}")
        com = mod.__dict__[f"{c.stem}".title()]
        bot.add_slash_command(com)

    return bot


if os.name != "nt":
    import uvloop

    uvloop.install()

if __name__ == "__main__":
    create_bot().run()
