import discord
from discord.ext import commands
import asyncio
from time import gmtime, strftime, localtime
import json
import config
import sqlite3 #this is for the db function

import ctypes
import ctypes.util
'''
This cog is for confirming the bot was logged in, and it will initialize a loop task that will be executed every 450 seconds to prevent the Heroku dino from putting the bot to sleep mode
'''
#TODO: Finish database function some day!!!!!
class manager(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.version = config.getVersion()
		self.backstage = int(config.getBackstage())

	@commands.Cog.listener()
	async def on_ready(self):
		print(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		channel = self.bot.get_channel(self.backstage)
		await channel.send(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		await self.bot.change_presence(activity = discord.Game(self.version))
		#db = sqlite3.connect('songlists.db') #not finished yet
		if (discord.opus.is_loaded()):
			print("Opus library loaded.")
		'''
		else:
			print("Manually looking for opus by using ctypes...")
			opus = ctypes.util.find_library('opus')
			print(opus)
			discord.opus.load_opus(opus)
			print(discord.opus.is_loaded())
		'''
		print("Ready.")


###loop tasks to keep heroku from putting my bot to sleep##
async def wakeup():
	while(1):
		a = 1 + 1  #yep, simple task to keep the bot up ;)
		await asyncio.sleep(450)

def setup(bot):
	bot.add_cog(manager(bot))
	print("Manager loaded.")
	bot.loop.create_task(wakeup())
	print("Wakeup periodic task initialized.")
