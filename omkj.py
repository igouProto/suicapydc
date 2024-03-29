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
		draw_comments = luck_elements["draw-comment"]
		charge_comments = luck_elements["charge-comment"]
	file.close()
except IOError as e:
	print("Failed to load luck components from json.")


def choiceluck(weight):
	numbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
	t = random.choices(numbers, weights=weight)
	return int(t[0])


def omkj_generate(id, author, force_random=False):
	time = datetime.now()
	seed = time.year * 10000 + (time.month + 1) * 100 + time.day + id

	if force_random:
		seed += (time.second + time.microsecond)

	random.seed(seed)
	# draw the results
	luck = choiceluck(weight)
	luckNum = random.randint(0, 500)
	colorindex = random.randint(0, (len(colors)-1))
	detindex = random.randint(0, (len(determinations)-1))
	drawIndex = random.randint(0, 10)
	draw_comment = draw_comments[drawIndex]
	payIndex = random.randint(0, 10)
	charge_comment = charge_comments[payIndex]
	dirIndex = random.randint(0, len(directions) - 1)
	direction = directions[dirIndex]
	serial = f"{seed}"  # showing the seed just for fun
	# the embed
	embed = discord.Embed(title="**{}**".format(fortune[luck]), description = str(determinations[detindex]) )
	embed.set_author(name=f'{author.display_name} 的每日占卜結果～', icon_url = author.avatar_url)

	embed.add_field(name='歐洲方位', value=directions[dirIndex], inline=True)
	embed.add_field(name='抽卡指數', value=f'{draw_comment} - ☆ {drawIndex}', inline=True)
	embed.add_field(name='課金指數', value=f'{charge_comment} - ☆ {payIndex}', inline=True)
	embed.add_field(name='幸運數', value=str(luckNum), inline=True)
	embed.add_field(name='幸運色', value=str(colors[colorindex]), inline=True)
	'''
	# alternative embed message
	luckString = f"歐洲方位：{directions[dirIndex]}\n" \
				 f"抽卡指數：☆ {drawIndex}\n" \
				 f"課金指數：☆ {payIndex}\n" \
				 f"幸運數：{luckNum}\n" \
				 f"幸運色：{colors[colorindex]}\n"
	embed.add_field(name="你今天的運氣指標", value=luckString)
	'''
	embed.set_footer(text="{} • {}".format(f"天不靈地不理御神籤第{serial}號", strftime('%y/%m/%d', localtime())))
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
	drawIndex = random.randint(0, 10)
	payIndex = random.randint(0, 10)
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
