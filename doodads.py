import time

import discord
from discord.ext import commands
import omkj
from datetime import datetime
from time import strftime, localtime
import requests
import urllib
import asyncio

# Kancolle recipe custom module
import lscGen
import rscGen

# Fake NKODICE module
import fake_nkodice

'''
This cog contains some doodads including a recipe generator for Kantai Collection, an omikuji function, honkai impact calendar, and a calculator that uses the math.js api"
'''


class doodads(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	def dice_embed(self, game: fake_nkodice.fake_nkodice) -> discord.Embed:

		selection = game.get_selection()
		status = game.get_status()
		u = game.get_U_score()
		m = game.get_M_score()
		c = game.get_C_score()
		score_adds = game.get_score_adds()
		u_add = score_adds[0]
		m_add = score_adds[1]
		c_add = score_adds[2]
		total = game.get_total_score()
		words = game.get_word_count()
		chances = game.get_chances()
		nudges_left = game.get_nugdes_left()
		rolls = game.get_rolls()

		embed = discord.Embed(title=f"{selection}", description=f"{status}")
		embed.set_author(name=f"{chances} ROLLS LEFT • {nudges_left} NUDGES LEFT")
		embed.add_field(name="U", value=f"{int(u)} ({u_add})", inline=True)
		embed.add_field(name="M", value=f"{int(m)} ({m_add})", inline=True)
		embed.add_field(name="C", value=f"{int(c)} ({c_add})", inline=True)
		embed.add_field(name="TOTAL", value=f"{int(total)}", inline=True)
		embed.add_field(name="WORDS", value=f"{words}", inline=True)
		embed.set_footer(text=f"Fake NKODICE - ROLL {rolls}")
		return embed

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
				result = f"出問題了owq (HTTP {r.status_code})"
				if r.content:
					result += f"\n({r.content.decode('utf-8')})"

			embed = discord.Embed(title=expression, description="= " + result)
			embed.set_author(name="可愛ㄉ計算小機機")
			embed.set_footer(text="簡單接了個免費的 math.js API。")
			await ctx.send(embed=embed)

	@commands.command(name="dice", aliases=['d', 'nkodice', 'nko'])  # low-cost copycat nkodice...
	async def _dice(self, ctx):
		# init
		game = fake_nkodice.fake_nkodice(player_id=ctx.message.author.id)
		embed = self.dice_embed(game=game)
		game_panel = await ctx.send(embed=embed)
		await game_panel.add_reaction('🎲')
		await game_panel.add_reaction('⏫')
		await game_panel.add_reaction('❌')

		def check(react, usr):
			if usr.bot:
				return False
			if react.message.guild.id != ctx.message.guild.id:  # prevent cross-guild remote control glitch
				return False
			elif react.message.guild.id == ctx.message.guild.id:  # i want to be more precise (idk if it helps tho)
				if usr.id == game.get_player_ID():
					return True
				else:
					return False
			else:
				return False

		reaction = None

		while True:
			if str(reaction) == '🎲':
				game.roll()
				await game_panel.edit(embed=self.dice_embed(game=game))
				while True:  # nudging
					if str(reaction) == '⏫':
						await game.nudge()
						await game_panel.edit(embed=self.dice_embed(game=game))
					try:
						reaction, user = await self.bot.wait_for('reaction_add', timeout=5, check=check)
						await game_panel.remove_reaction(reaction, user)
					except:
						break
				await game.score_calc()
				await game_panel.edit(embed=self.dice_embed(game=game))
				if game.ochinchin:
					pass  # await ctx.send(f"襪幹，<@{ctx.message.author.id}>骰出了OCHINCHIN！！！")
				if game.get_chances() <= 0:
					break
			elif str(reaction) == '❌':
				break
			try:
				reaction, user = await self.bot.wait_for('reaction_add', timeout=300, check=check)
				await game_panel.remove_reaction(reaction, user)
			except:  # when in doubt, break. whatever.
				break
		await game_panel.clear_reactions()
		await asyncio.sleep(2)
		embed = discord.Embed(title=f"{game.get_total_score()}")
		embed.add_field(name='Rolls', value=game.get_rolls(), inline=True)
		embed.add_field(name='Nudges', value=game.get_nudges(), inline=True)
		embed.add_field(name='Words', value=game.get_word_count(), inline=True)
		embed.add_field(name='Ochinchin', value=game.get_ochinchin_count(), inline=True)
		embed.set_author(name=f"Fake NKODICE")
		embed.set_footer(text="GAME OVER!")
		await game_panel.edit(embed=embed)



def setup(bot):
	bot.add_cog(doodads(bot))
	print("doodads loaded.")

