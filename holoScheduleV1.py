import discord
from discord.ext import commands
import asyncio
from discord.utils import get
from discord.ext.commands import CommandNotFound

import requests
from bs4 import BeautifulSoup

class holoScheduleV1(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = "holoschedule", aliases = ['holo', 'h'])
	async def _holoschedule(self, ctx):
		await ctx.trigger_typing()
		headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:61.0) Gecko/20100101 Firefox/61.0'}
		url = "https://virtual-youtuber.userlocal.jp/office/cover" #sorry for directly scrapping, will use youtube API later
		data = requests.get(url, headers = headers)
		soup = BeautifulSoup(data.text, 'lxml')
		divs = soup.findAll('div', {"class", "card card-live"}, recursive=True)
		'''for my reference only
		for item in divs:
			print(item['data-channel-link'])
			print(item['data-link'])
			print(item['data-name'])
			print(item['data-title'])
			print("---")
		'''
		embed=discord.Embed()
		embed.set_author(name = "HoloLIVE!", icon_url = self.bot.user.avatar_url)
		for item in divs:
			embed.add_field(name="**{}**".format(item['data-name']), value="[{}]({})".format(item['data-title'], item['data-link']), inline=False)
		embed.set_footer(text = "資料來源：https://virtual-youtuber.userlocal.jp/office/cover")
		await ctx.send(embed = embed)

def setup(bot):
	bot.add_cog(holoScheduleV1(bot))
	print("HOLOLIVE schedule viewer loaded.")
