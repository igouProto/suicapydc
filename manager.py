import discord
from discord.ext import commands
import asyncio
from time import gmtime, strftime, localtime
import config
import sqlite3  # this is for the db function
from discord.ext.commands import CommandNotFound

'''
This cog is for confirming the bot was logged in, and it will initialize a loop task that will be executed every 450 seconds to prevent the Heroku dino from putting the bot to sleep mode
'''
# TODO: Finish database function some day!!!!!


class manager(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.version = config.getVersion()  # remember to change this
		self.backstage = int(config.getBackstage())

	@commands.Cog.listener()
	async def on_ready(self):
		print(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		channel = self.bot.get_channel(self.backstage)
		await channel.send(strftime('Bot logged in at %Y/%m/%d, %H:%M:%S', localtime()))
		await self.bot.change_presence(activity = discord.Game(f'SUICA {self.version}'))
		# db = sqlite3.connect('songlists.db')  # not finished yet
		print(f'Version: {self.version}')
		print("Ready.")

	@commands.Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, CommandNotFound):
			# if ctx.message.toString.count('.') >= 2:
			# 	pass
			embed = discord.Embed(title=':x: 糟了個糕。', colour=0xff0000)
			embed.description = "你好像打錯字囉。"
			embed.set_footer(text=error)
			await ctx.send(embed=embed)
		if isinstance(error, commands.CheckFailure):
			await ctx.send(':x:權限不足或操作人員非應用程式擁有者。')
		else:
			raise error
'''
###loop tasks to keep heroku from putting my bot to sleep## no need i moved to my own machine :D
async def wakeup():
	while(1):
		a = 1 + 1  #yep, simple task to keep the bot up ;)
		await asyncio.sleep(450)
'''

def setup(bot):
	bot.add_cog(manager(bot))
	print("Manager loaded.")
	# bot.loop.create_task(wakeup())
	# print("Wakeup periodic task initialized.")
