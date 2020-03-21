import random
from datetime import datetime

def cv(today, ID):
	random.seed(ID)
	result = []
	oil = [4000, 3500, 4000, 4000]
	amo = [2000, 3500, 2000, 2000]
	kou = [5000, 6000, 5000, 5000]
	bau = [6500, 6000, 5200, 6500]
	index = random.randint(0,3)
	result.append(int(oil[index]) + random.randint(31, today) % 49 * 10)
	result.append(int(amo[index]) + random.randint(37, today) % 49 * 10)
	result.append(int(kou[index]) + random.randint(91, today) % 49 * 10)
	result.append(int(bau[index]) + random.randint(101, today) % 49 * 10)
	r5 = random.randint(11, today) % 10 + 1
	if r5 <= 4 and r5 > 0:
		result.append(1)
	elif r5 <= 8 and r5 > 4:
		result.append(20)
	else:
		result.append(100)
	print(result)
	return result

def bb(today, ID):
	random.seed(ID)
	result = []
	oil = [4000, 4000, 6000, 4000]
	amo = [6000, 6000, 5000, 6000]
	kou = [6000, 6000, 6000, 6000]
	bau = [3000, 2000, 2000, 3000]
	index = random.randint(0,3)
	result.append(int(oil[index]) + random.randint(73, today) % 49 * 10)
	result.append(int(amo[index]) + random.randint(61, today) % 49 * 10)
	result.append(int(kou[index]) + random.randint(59, today) % 49 * 10)
	result.append(int(bau[index]) + random.randint(89, today) % 49 * 10)
	r5 = random.randint(7, today) % 10 + 1
	if r5 <= 4 and r5 > 0:
		result.append(1)
	elif r5 <= 8 and r5 > 4:
		result.append(20)
	else:
		result.append(100)
	print(result)
	return result

