import discord
from discord.ext import commands
import random
from datetime import datetime
import omkj
import json
'''
This cog contains commands that are so called "luck-related," including the Omikuji function and the "Honkai 3 calendar function."
'''
class luckyDraws(commands.Cog):

	def __init__(self, bot):
		self.bot = bot

	@commands.command(name = "b3c", aliases = ['bh3', 'bh3cal', 'bc'])  #"Honkai 3 calendar"
	async def _bh3calendar(self, ctx):
		await ctx.trigger_typing()
		embed = omkj.b3c_cal(ctx.message.author.id)
		await ctx.send(embed = embed)
		
	###OMIKUJI###
	@commands.command(name = "omikuji", aliases = ['omkj'])  #Omikuji function that follows real-life occurrence of luck index :D
	async def _omikuji(self, ctx):
		await ctx.trigger_typing()
		author = ctx.message.author 
		embed = omkj.omkj_generate(author.id, author)
		await ctx.send(embed = embed)

def setup(bot):
	bot.add_cog(luckyDraws(bot))
	print("Omikuji + BH3CAL module loaded.")

