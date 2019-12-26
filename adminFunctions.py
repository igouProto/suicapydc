#discord py modules
import discord
from discord.ext import commands
import asyncio
from discord.utils import get
from discord.ext.commands import CommandNotFound
import json
import os
import sys

#TODO (igouP): Author ID (my own ID) is still hardcoded.
#			   Add a function that allows others to add another announcement channel.
#			   Write more about this cog!
class adminFunctions(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = "ping")  #ping function, used for testing the bot's respond time
	async def _ping(self, ctx):
			t = await ctx.send('現在的反應時間是.........')
			ms = (t.created_at - ctx.message.created_at).total_seconds() * 1000
			await t.edit(content = '現在的反應時間是.........**{}**ms'.format(int(ms)))

	@commands.command(name = "restart", aliases = ['res']) #restart the bot
	async def _restart(self, ctx):
		if ctx.message.author.id == 368468314378469379:
			await self.bot.change_presence(activity = discord.Game(name = '重新啟動中'))
			await ctx.send('正在重新啟動...')
			os.execl(sys.executable, sys.executable, *sys.argv)

	@commands.command(name = "upannounce", aliases = ['upd'])  #This is used for me to
	async def _upannounce(self, ctx):
		if ctx.message.author.id == 368468314378469379:
			await ctx.send("輸入公告內容或輸入cancel取消。")
			channel = ctx.message.channel

			def check(author):
				def messageCheck(message):
					if author != message.author:
						return False
					else:
						return True
				return messageCheck

			try:
				message = await self.bot.wait_for('message', check = check(ctx.message.author), timeout = 120)  #wait for the announcement content, will time out after 120 secs.
			except asyncio.TimeoutError:
				await channel.send('操作逾時。')
			else:
				announcement = message.content
				try:
					if (announcement == 'cancel'):  #cancel the operation if 'cancel' is entered in the announcement
						await ctx.send('操作已取消。')
						return
					else:
						with open('announce_channels.json') as file:
							channels = json.load(file)
							channel_list = channels["channels"]  #read all the channel id's written in the list
							for each in channel_list:
								await self.bot.get_channel(each).send(announcement)  #and send the announcement to all the channels
						file.close()
						await ctx.send('已發出更新公告。')
				except IOError as e:
					ctx.send("無法讀取公告頻道清單。")
		else:
			return

	@commands.command(name = "about")  
	async def _about(self, ctx):
		await ctx.trigger_typing()
		#retrive the discord app information
		self.bot.appinfo = await self.bot.application_info()
		self.bot.userinfo = await self.bot.fetch_user(474090871214702593)
		self.botid = self.bot.appinfo.id
		name = self.bot.appinfo.name
		owner = self.bot.appinfo.owner.mention
		borntime = self.bot.userinfo.created_at
		await ctx.send('ID:{}\n應用程式名稱：{}\n作者：{}\n建置時間：{}\n'.format(self.botid, name, owner, borntime))

	@commands.command(name = "purge")  #delete messages, allowing at most 15 messages at a time (typos can be hazardous, really.)
	async def _purge(self, ctx, amount:int):
		if ctx.message.author.id == 368468314378469379:
			if amount >= 15:
				amount = 15
			await ctx.message.channel.purge(limit = amount)
			cmd = ctx.message
			msg = await ctx.send('已清除包含指令在內的**{}**則訊息'.format(amount))
			await asyncio.sleep(1)
			await msg.delete()

	@commands.command(name = "port")  #change 'portal' destination, the 'portal' is defined in messageHandler.py
	async def _port(self, ctx, dest:int):
		message_handler = self.bot.get_cog('messageHandler')
		if ctx.message.author.id == 368468314378469379:
			message_handler.set_destination(dest)
			destination = message_handler.get_destination()
			await ctx.send('傳聲筒目的地已設為**{}** - {}'.format(self.bot.get_channel(destination).name, self.bot.get_channel(destination).guild.name))

def setup(bot):
	bot.add_cog(adminFunctions(bot))
	print("Admin functions loaded.")
