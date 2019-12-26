import discord
import random
from datetime import datetime
from time import gmtime, strftime, localtime
import json

'''
This module is responsible for generating the Omikuji result and "Honkai 3 calendar" result.
'''

try:
	with open('omikuji.json') as file:
		luck_elements = json.load(file)
		weight = luck_elements["weight"]
		fortune = luck_elements["fortune"]
		colors = luck_elements["colors"]
		determinations = luck_elements["determinations"]
		directions = luck_elements["directions"]
		bh3cal = luck_elements["bh3cal"]
	file.close()
except IOError as e:
	print("Failed to load luck components from json.")


def choiceluck(weight):
	t = random.randint(0, sum(weight) - 1)
	for i, val in enumerate(weight):
		t -= val
		if t < 0:
			return i

def omkj_generate(id, author):
	time = datetime.now()
	seedIndex = int(id) + time.year * 10000 + time.year * 10000 + (time.month + 1) * 100 + time.day
	random.seed(seedIndex)
	##display result
	luck = fortune[choiceluck(weight)]
	luckNum = random.randint(0,9)
	colorindex = random.randint(0, (len(colors)-1))
	detindex = random.randint(0, (len(determinations)-1))
	#the embed
	embed = discord.Embed(title="**{}**".format(str(luck)), description = str(determinations[detindex]) )
	embed.set_author(name = '{}的每日占卜結果～'.format(author.display_name), icon_url = author.avatar_url)
	embed.add_field(name='幸運數', value=luckNum, inline=True)
	embed.add_field(name='幸運色', value=str(colors[colorindex]), inline=True)
	embed.set_footer(text="{}".format(strftime('%Y/%m/%d', localtime())))

	return embed

def b3c_cal(id):
	now = datetime.now()
	seed = now.year * 10000 + (now.month + 1) * 100 + now.day + int(id)
	random.seed(seed)
	#draw out the events
	eventPool = bh3cal
	eventToday = []
	while len(eventToday) < 2:
		ev = eventPool[random.randint(0, len(eventPool) - 1)]
		if ev not in eventToday:
			eventToday.append(ev)
	random.shuffle(eventToday)
	evGood = eventToday[0]
	evbad = eventToday[1]
	#draw index and pay index for today
	drawIndex = random.randint(0, 10) * 0.5
	payIndex = random.randint(0, 10) * 0.5
	#the direction of seat
	direction = directions[random.randint(0, len(directions) - 1)]
	#the embed
	embed = discord.Embed(title = '今天是 {} 年 {} 月 {} 日'.format(now.year, now.month, now.day))
	embed.set_author(name = '崩崩崩老黃曆')
	embed.add_field(name = '宜', value = evGood, inline = False)
	embed.add_field(name = '不宜', value = evbad, inline = False)
	embed.add_field(name = '抽卡指數', value = '☆{0:0.1f}'.format(drawIndex), inline = True)
	embed.add_field(name = '課金指數', value = '☆{0:0.1f}'.format(payIndex), inline = True)
	dirText = '建議面向**{}**方抽卡，離歐洲最近。'.format(direction)
	embed.add_field(name = '座位面向', value = dirText, inline = False)
	
	return embed
