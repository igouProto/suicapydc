from discord.ext import commands
import config  # custom config module

'''
This is the main program of the bot, it creates a bot instance and loads all the extensions then finally run it.
'''

###STARTUP###
print("Booting SUICA...")
bot = commands.Bot(command_prefix=config.getPrefix())
TOKEN = config.getToken()
config.version = '2.1.1'

# TODO (igouP): Gather all the extensions and use one single statement to load all of them.
bot.load_extension('manager')
bot.load_extension('adminFunctions')
bot.load_extension('messageHandler')
bot.load_extension('musicPlayer_wavelink')
# bot.load_extension('musicPlayer')  # dead
bot.load_extension('luckyDraws')
bot.load_extension('kancolle')
# bot.load_extension('holoScheduleV1')  # dead

###BASIC COMMANDS (To make sure the bot is alive)###
'''
Well, come to think of it, maybe the main function should not contain any command if commands are now sorted in cogs...?
note to self: ping and manual are moved to adminFunctions.py
'''

###RUN THE BOT!!!###
bot.run(TOKEN)
