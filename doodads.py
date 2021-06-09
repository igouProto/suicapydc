import discord
from discord.ext import commands
import omkj
from datetime import datetime
from time import strftime, localtime
import requests
import urllib

# Kancolle recipe custom module
import lscGen
import rscGen

'''
This cog contains some doodads including a recipe generator for Kantai Collection, an omikuji function, honkai impact calendar, and a calculator that uses the math.js api"
'''


class doodads(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = "lsc")
	async def _lsc(self, ctx, arg: str = None):
		print (arg)
		await ctx.trigger_typing()
		if arg == None:
			await ctx.send('指令 **.lsc**（大型艦建造玄學配方產生）使用方法：\n' + '```.lsc <艦種代號>\n\n艦種代號：\ncv 航空母艦\nbb 戰艦```')
			return
		now = datetime.now()
		today = now.year * 10000 + (now.month + 1) * 100 + now.day
		authorID = ctx.message.author.id
		if arg.lower() == 'cv':
			result = lscGen.cv(today, authorID) #len = 5, oil/ammo/kou/bau/shizai
			embedDesc = "航空母艦"
		elif arg.lower() == 'bb':
			result = lscGen.bb(today, authorID) #len = 5, oil/ammo/kou/bau/shizai
			embedDesc = "戰艦"
		embed = discord.Embed(title="提督今天的大造玄學配方", description=embedDesc)
		embed.add_field(name = '燃料/彈藥/鋼材/鋁土 (開發資材)' , value = '**{}/{}/{}/{} ({})**'.format(result[0], result[1], result[2], result[3], result[4]) , inline=True)
		embed.set_footer(text="{}".format(strftime('%Y/%m/%d', localtime())))
		await ctx.send(embed = embed)

	@commands.command(name = "rsc")
	async def _rsc(self, ctx, arg: str = None):
		await ctx.trigger_typing()
		if arg == None:
			await ctx.send('指令 **.rsc**（通常建造玄學配方產生）使用方法：\n' + '```.rsc <艦種代號>\n\n艦種代號：\ndd 驅逐艦\ncl 輕巡洋艦\nca 重巡洋艦\ncv 航空母艦\nbb 戰艦\nss 潛水艇```')
			return
		now = datetime.now()
		today = now.year * 10000 + (now.month + 1) * 100 + now.day
		authorID = ctx.message.author.id
		if arg.lower() == 'dd':
			result = rscGen.dd(today, authorID)
			embedDesc = '驅逐艦'
		elif arg.lower() == 'cl':
			result = rscGen.cl(today, authorID)
			embedDesc = '輕巡洋艦'
		elif arg.lower() == 'ca':
			result = rscGen.ca(today, authorID)
			embedDesc = '重巡洋艦'
		elif arg.lower() == 'bb':
			result = rscGen.bb(today, authorID)
			embedDesc = '戰艦'
		elif arg.lower() == 'cv':
			result = rscGen.cv(today, authorID)
			embedDesc = '航空母艦'
		elif arg.lower() == 'ss':
			result = rscGen.ss(today, authorID)
			embedDesc = '潛水艇'
		recipe = '**{}/{}/{}/{}**'.format(result[0][0], result[0][1], result[0][2], result[0][3])
		recipeS = '**{}/{}/{}/{}**'.format(result[1][0], result[1][1], result[1][2], result[1][3])
		embed=discord.Embed(title="提督今天的通常建造玄學配方", description=embedDesc)
		embed.add_field(name='燃料/彈藥/鋼材/鋁土', value=recipe, inline=False)
		embed.add_field(name='加一點玄學的話', value=recipeS, inline=False)
		embed.set_footer(text="{}".format(strftime('%Y/%m/%d', localtime())))
		await ctx.send(embed = embed)

	@commands.command(name = "b3c", aliases = ['bh3', 'bh3cal', 'bc'])  # "Honkai 3 calendar"
	async def _bh3calendar(self, ctx):
		await ctx.trigger_typing()
		embed = omkj.b3c_cal(ctx.message.author.id)
		await ctx.send(embed = embed)

	@commands.command(name = "omikuji", aliases = ['omkj'])  # Omikuji function that follows real-life occurrence of luck index :D
	async def _omikuji(self, ctx, *args):
		await ctx.trigger_typing()
		author = ctx.message.author
		if 'r' in args:
			embed = omkj.omkj_generate(author.id, author, True)
		else:
			embed = omkj.omkj_generate(author.id, author)
		await ctx.send(embed = embed)

	@commands.command(name="calculator", aliases = ['calc', 'c'])  # calculator! But I can't make one so I'm using the math.js api!
	async def _calculator(self, ctx, *expr: str):
		if expr:
			await ctx.trigger_typing()
			expression = ''.join(expr)
			expr_url = urllib.parse.quote_plus(expression)
			request = "http://api.mathjs.org/v4/?expr=" + expr_url
			r = requests.get(request)
			if r.status_code == requests.codes.ok:
				result = r.text
			else:
				result = "出問題了owq"

			embed = discord.Embed(title=expression, description="= " + result)
			embed.set_author(name="可愛ㄉ計算小機機")
			embed.set_footer(text="簡單接了個免費的 math.js API。")
			await ctx.send(embed=embed)


def setup(bot):
	bot.add_cog(doodads(bot))
	print("doodads loaded.")

