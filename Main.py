import asyncio
import discord
from discord.ext import commands
from discord.utils import get
from discord.ext.commands import CommandNotFound
import config  #custom config module

'''
This is the main program of the bot, basically it creates a bot instance and loads all the extensions then finally run it.
there are 2 basic functions in the main program:
hello: says hello to the user, used for testing whether the bot listens to commands or not.
manual: prints out the manual of this bot
'''

###STARTUP###
print("Booting SUICA...")
bot = commands.Bot(command_prefix = config.getPrefix())
TOKEN = config.getToken()

#TODO (igouP): Gather all the extensions and use one single statement to load all of them.
#			   And fix the Kancolle functions.
bot.load_extension('manager')
bot.load_extension('adminFunctions')
bot.load_extension('messageHandler')
bot.load_extension('musicPlayer')
bot.load_extension('luckyDraws')
#bot.load_extension('kancolle')  #currently not working, will fix it one day

bot.remove_command('help') #I want my own help cmd.

###BASIC COMMANDS (To make sure the bot's alive)###
@bot.command(name = "hello")  #greets to you!
async def _hello(ctx):
	msg = 'Hello {0.author.mention}'.format(ctx.message)
	await ctx.send(msg)

@bot.command(name = "manual", aliases = ['man', 'help']) #print the manual out
async def _manual(ctx):
	manual = open('help.txt', 'r')
	msg = manual.read()
	await ctx.send(msg)
	manual.close()

###RUN THE BOT!!!###
bot.run(TOKEN)