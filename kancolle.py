import discord
from discord.ext import commands
from datetime import datetime
from time import gmtime, strftime, localtime
#Kancolle recipe custom module
import lscGen
import rscGen
'''
This cog contains commands that generates recipes for Kantai collection"
'''
#TODO (igouP): THIS FUNCTION IS BROKEN :(
class kancolle(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	###KANCOLLE RECIPE GENERATOR###
	###LSC###
	@commands.command(name = "lsc")
	async def _lsc(self, ctx, arg: str = None):
		print (arg)
		await ctx.trigger_typing()
		if arg == None:
			await ctx.send('指令 **.lsc**（大型艦建造玄學配方產生）使用方法：\n' + '```.lsc <艦種代號>\n\n艦種代號：\n-cv 航空母艦\n-bb 戰艦```')
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

	###RSC###
	@commands.command(name = "rsc")
	async def _rsc(self, ctx, arg: str = None):
		await ctx.trigger_typing()
		if arg == None:
			await ctx.send('指令 **.rsc**（通常建造玄學配方產生）使用方法：\n' + '```.rsc <艦種代號>\n\n艦種代號：\n-dd 驅逐艦\n-cl 輕巡洋艦\n-ca 重巡洋艦\n-cv 航空母艦\n-bb 戰艦\n-ss 潛水艇```')
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
		elif arg.lower() == '-ss':
			result = rscGen.ss(today, authorID)
			embedDesc = '潛水艇'
		recipe = '**{}/{}/{}/{}**'.format(result[0][0], result[0][1], result[0][2], result[0][3])
		recipeS = '**{}/{}/{}/{}**'.format(result[1][0], result[1][1], result[1][2], result[1][3])
		embed=discord.Embed(title="提督今天的通常建造玄學配方", description=embedDesc)
		embed.add_field(name='燃料/彈藥/鋼材/鋁土', value=recipe, inline=False)
		embed.add_field(name='加一點玄學的話', value=recipeS, inline=False)
		embed.set_footer(text="{}".format(strftime('%Y/%m/%d', localtime())))
		await ctx.send(embed = embed)

def setup(bot):
	bot.add_cog(kancolle(bot))
	print("Kancolle recipe generator loaded.")