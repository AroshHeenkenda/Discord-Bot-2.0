"""
Author: Arosh Heenkenda
Created: 12/01/2022
Edited: 12/02/2022
Purpose: Main setup for the discord bot
"""

#IMPORTS
from pathlib import Path
import discord
from discord.ext import commands

#Constants
PREFIX = "##"
OWNER_IDS = [443360265141092352]

class AroshBot(commands.Bot):
    def __init__(self):
        self._cogs = [p.stem for p in Path(".").glob("./bot/cogs/*.py")]


        #case insensitive ensures that both !play and !Play work
        super().__init__(
            command_prefix=self.prefix,
            case_insensitive=True,
            intents=discord.Intents.all()
        )

        #Can also set the intents like so:
        #intents = discord.Intents.default()
        #intents.members = True

    def setup(self):
        print("Running setup...")

        for cog in self._cogs:
            self.load_extension(f"bot.cogs.{cog}")
            print(f" Loaded '{cog}' cog.")

        print("Setup complete.")

    def run(self):
        self.setup()

        #Loading in the token
        with open("data/token.0", "r", encoding="utf-8") as f:
            TOKEN = f.read()
        #TOKEN =   # Bot token

        print("Running bot...")
        super().run(TOKEN, reconnect=True) #Reconnect will try to reconnect to discord if it fails

    #Shutting down the bot
    async def shutdown(self):
        print("Closing connection to Discord...")
        await super.close()
        #await super.close() -> also works
        #await self.logout() -> also works

    async def close(self):
        print("Closing on keyboard interrupt...")
        await self.shutdown()

    async def on_connect(self):
        print(f"Connected to Discord (latency: {self.latency*1000:,.0f} ms).")

    async def on_resumed(self):
        print("Bot resumed.")

    async def on_disconnect(self):
        print("Bot disconnected.")

    #async def on_error(self, err, *args, **kwargs):
    #    raise
    #
    #async def on_command_error(self, ctx, exc):
    #    raise getattr(exc, "original", exc)

    async def on_ready(self):
        self.client_id = (await self.application_info()).id #client ID
        print("Bot ready.")

    #Setting the prefix
    async def prefix(self, bot, msg):
        return commands.when_mentioned_or(PREFIX)(bot, msg) #returns callable, so need to call callable

    async def process_commands(self, msg):
        ctx = await self.get_context(msg, cls=commands.Context)

        if ctx.command is not None:
            await self.invoke(ctx)

    async def on_message(self, msg):
        if not msg.author.bot:
            await self.process_commands(msg)
