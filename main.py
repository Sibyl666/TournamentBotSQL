import discord
from discord.ext import commands

import json

from os import listdir
from os.path import isfile, join

import traceback

with open('config.json') as config_file:
    data = json.load(config_file)

bot = commands.Bot(command_prefix=data["command_prefix"])

if __name__ == '__main__':
    for extension in [f.replace('.py', '') for f in listdir(data["cogs_dir"]) if isfile(join(data["cogs_dir"], f))]:
        try:
            bot.load_extension(data["cogs_dir"] + "." + extension)
        except (discord.ClientException, ModuleNotFoundError):
            print(f'Failed to load extension {extension}.')
            traceback.print_exc()


@bot.event
async def on_ready():
    print(f'\n\nLogged in as: {bot.user.name} - {bot.user.id}\nVersion: {discord.__version__}\n')
    print(f'Successfully logged in and booted...!')


bot.run(data["bot_token"], bot=True, reconnect=True)
