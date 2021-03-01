import discord
from discord.ext import commands
from time import gmtime, strftime, localtime
import config
import sqlite3  # this is for the db function
from discord.ext.commands import CommandNotFound

'''
This cog is for confirming the bot was logged in, handling general command errors, and debug/keyword reply toggles.
'''
# TODO: Finish database function some day!!!!!(or not)


class manager(commands.Cog):
	def __init__(self, bot):
		self.bot = bot
		self.version = config.getVersion()
		self.backstage = int(config.getBackstage())

		self.debug = False

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
			# await ctx.send(':x:權限不足或操作人員非應用程式擁有者。')
			await ctx.message.add_reaction("⛔")
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

	@commands.is_owner()
	@commands.command(name='msghandleroff', aliases=['msgoff'])
	async def _msghandleroff(self, ctx):
		self.bot.unload_extension('messageHandler')
		await ctx.send('已關閉關鍵字回覆。')

	@commands.is_owner()
	@commands.command(name='msghandleron', aliases=['msgon'])
	async def _msghandleron(self, ctx):
		self.bot.load_extension('messageHandler')
		await ctx.send('已開啟關鍵字回覆。')
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
