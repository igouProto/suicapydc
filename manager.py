import asyncio

import discord
from discord.ext import commands
from time import gmtime, strftime, localtime
import config
import sqlite3  # this is for the db function
from discord.ext.commands import CommandNotFound

import requests

# for periodic restart test
import schedule
import os
import sys

import musicPlayer_wavelink

'''
This cog is for confirming the bot was logged in, handling general command errors, and debug/keyword reply toggles.
'''
# TODO: Finish database function some day!!!!!(or not)


class manager(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.version = config.getVersion()
		self.backstage = int(config.getBackstage())
		# self.error_channel = int(config.getErrChannel())

		self.debug = True

	@commands.Cog.listener()
	async def on_ready(self):
		print(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		channel = self.bot.get_channel(self.backstage)
		await channel.send(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		await self.bot.change_presence(activity=discord.Game(f'SUICA {self.version}'))
		# db = sqlite3.connect('songlists.db')  # not finished yet
		print(f'Version: {self.version}')
		print("Ready.")

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, CommandNotFound):
			if ctx.message.content.count('.') >= 2:
				return
			await ctx.message.add_reaction("❓")
		if isinstance(error, commands.CheckFailure):
			await ctx.message.add_reaction("❓")  # shh...just pretend the bot doesn't know these commands
		else:
			if self.debug:
				raise error

	@commands.is_owner()
	@commands.command(name='debug')  # i want to keep my terminal clean
	async def _debug(self, ctx):
		if self.debug:
			self.debug = False
			await ctx.send('偵錯模式已關閉。')
		else:
			self.debug = True
			await ctx.send('偵錯模式已開啟，查看後台以獲取錯誤訊息。')


# loop tasks to keep heroku from putting my bot to sleep
async def wakeup():
	while(1):
		a = 1 + 1  # yep, simple task to keep the bot up ;)
		requests.post("https://suicalavalink.herokuapp.com")
		await asyncio.sleep(500)


async def start_schedule_task():
	while(1):
		schedule.run_pending()
		await asyncio.sleep(1)


def restart():
	os.execl(sys.executable, sys.executable, *sys.argv)


def setup(bot):
	bot.add_cog(manager(bot))
	print("Manager loaded.")
	#bot.loop.create_task(wakeup())
	#print("Wakeup periodic task initialized.")

	#schedule.every().day.at(config.getRestartTime()).do(restart)
	#bot.loop.create_task(start_schedule_task())

	#print("Schedule task initiated.")

