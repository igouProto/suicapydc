import random
from datetime import datetime

def dd(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [30, 250, 270, 270]
	amo = [30, 30, 150, 130]
	kou = [30, 200, 370, 330]
	bau = [30, 30, 50, 30]
	index = random.randint(0,3)
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,9))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,9))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 2:
		resultS.append(int(oil[index]) + random.randint(0,29))
		resultS.append(int(amo[index]) + random.randint(0,49))
		resultS.append(int(kou[index]) + random.randint(0,29))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 3:
		resultS.append(int(oil[index]) + random.randint(0,29))
		resultS.append(int(amo[index]) + random.randint(0,69))
		resultS.append(int(kou[index]) + random.randint(0,69))
		resultS.append(int(bau[index]) + random.randint(0,9))
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result

def cl(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [30, 250]
	amo = [30, 30]
	kou = [30, 200]
	bau = [30, 30]
	index = random.randint(0,1)
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,9))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,9))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result

def ca(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [250, 270, 400]
	amo = [30, 130, 30]
	kou = [200, 330, 600]
	bau = [30, 30, 30]
	index = random.randint(0,2)
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,29))
		resultS.append(int(amo[index]) + random.randint(0,49))
		resultS.append(int(kou[index]) + random.randint(0,29))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 2:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result

def bb(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [400, 400, 400, 400, 400, 400, 520]
	amo = [30, 100, 100, 600, 700, 999, 130]
	kou = [600, 600, 700, 600, 600, 750, 680]
	bau = [30, 30, 30, 30, 30, 50, 40]
	index = random.randint(0,6)	
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 2:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 3:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))		
	elif index == 4:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 5:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,0))
		resultS.append(int(kou[index]) + random.randint(0,49))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 6:
		resultS.append(int(oil[index]) + random.randint(0,79))
		resultS.append(int(amo[index]) + random.randint(0,69))
		resultS.append(int(kou[index]) + random.randint(0,19))
		resultS.append(int(bau[index]) + random.randint(0,9))
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result

def cv(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [300, 350, 300, 300, 400, 300, 301]
	amo = [30, 30, 30, 30, 200, 300, 31]
	kou = [400, 400, 600, 999, 500, 600, 502]
	bau = [300, 350, 400, 400, 700, 600, 400]
	index = random.randint(0,6)
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,49))
	elif index == 2:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,99))
	elif index == 3:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,0))
		resultS.append(int(bau[index]) + random.randint(0,99))		
	elif index == 4:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,99))
	elif index == 5:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,99))
	elif index == 6:
		resultS.append(int(oil[index]) + random.randint(0,98))
		resultS.append(int(amo[index]) + random.randint(0,8))
		resultS.append(int(kou[index]) + random.randint(0,98))
		resultS.append(int(bau[index]) + random.randint(0,99))
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result

def ss(today, ID):
	random.seed(ID)
	result = []
	resultS = []
	#base recipe
	oil = [250, 250, 300, 270]
	amo = [30, 130, 100, 130]
	kou = [200, 200, 200, 330]
	bau = [30, 30, 30, 30]
	index = random.randint(0,2)
	#generate regular recipe
	result.append(int(oil[index]))
	result.append(int(amo[index]))
	result.append(int(kou[index]))
	result.append(int(bau[index]))
	#add some luck in it
	if index == 0:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,49))
	elif index == 1:
		resultS.append(int(oil[index]) + random.randint(0,49))
		resultS.append(int(amo[index]) + random.randint(0,9))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,49))
	elif index == 2:
		resultS.append(int(oil[index]) + random.randint(0,99))
		resultS.append(int(amo[index]) + random.randint(0,99))
		resultS.append(int(kou[index]) + random.randint(0,99))
		resultS.append(int(bau[index]) + random.randint(0,9))
	elif index == 3:
		resultS.append(int(oil[index]) + random.randint(0,29))
		resultS.append(int(amo[index]) + random.randint(0,69))
		resultS.append(int(kou[index]) + random.randint(0,69))
		resultS.append(int(bau[index]) + random.randint(0,9))		
	final_result = []
	final_result.append(result)
	final_result.append(resultS)
	print(final_result)
	return final_result








