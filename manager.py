import discord
from discord.ext import commands
import asyncio
from time import gmtime, strftime, localtime
import json
import config
'''
This cog is for confirming the bot was logged in, and it will initialize a loop task that will be executed every 450 seconds to prevent the Heroku dino from putting the bot to sleep mode
'''
class manager(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.version = config.getVersion()

	@commands.Cog.listener()
	async def on_ready(self):
		print(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		channel = self.bot.get_channel(474118233130270721)
		await channel.send(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		await self.bot.change_presence(activity = discord.Game(self.version))
		if (discord.opus.is_loaded()):
			print ("Opus library loaded.")
		print("Ready.")


###loop tasks to keep heroku from making my bot sleep##
async def wakeup():
	while(1):
		a = 1 + 1  #yep, simple task to keep the bot up ;)
		await asyncio.sleep(450)

def setup(bot):
	bot.add_cog(manager(bot))
	print("Manager loaded.")
	bot.loop.create_task(wakeup())
	print("Wakeup periodic task initialized.")
