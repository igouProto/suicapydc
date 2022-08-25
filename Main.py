from discord.ext import commands
import config  # custom config module
import json


'''
This is the main program of the bot, it creates a bot instance, loads all the extensions, and finally run it.
'''

# Startup
print("Booting SUICA...")  # totally unnecessary but makes the booting sequence look cooler UwU
bot = commands.Bot(command_prefix=config.getDefaultPrefix())
TOKEN = config.getToken()
config.version = '2.13.8-aws'

# TODO (igouP): Gather all the extensions and use one single statement to load all of them.
bot.load_extension('manager')
bot.load_extension('adminFunctions')
bot.load_extension('messageHandler')
bot.load_extension('musicPlayer_wavelink')
# bot.load_extension('musicPlayer_new')
bot.load_extension('doodads')
bot.load_extension('stonks')

bot.run(TOKEN)
