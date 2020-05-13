import discord
from discord.ext import commands

from database import Database

from os import listdir
from os.path import isfile, join

import traceback

cfg = Database.get_config()

bot = commands.Bot(command_prefix=cfg["command_prefix"])

if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(cfg["cogs_dir"]) if isfile(join(cfg["cogs_dir"], f))]:
        try:
            bot.load_extension(cfg["cogs_dir"] + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Successfully logged in and booted...!')


bot.run(cfg["bot_token"], bot=True, reconnect=True)
