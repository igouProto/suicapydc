import os
import json
'''
This module retrieves the essentials for the bot to run, including the token, command prefix and version information
'''
def getToken():
	try:
		with open('config.json', 'r') as file:
			configs = json.load(file)
			token = configs["token"]
			print("Token loaded from config.json: {}".format(token))
	except IOError as e:
		token = os.environ["TOKEN"]
		print("Token loaded from os environment variable: {}".format(token))
	return token

def getPrefix():
	try:
		with open('config.json', 'r') as file:
			configs = json.load(file)
			prefix = configs["prefix"]
			print("Prefix loaded from config.json: \'{}\'".format(prefix))
	except IOError as e:
		prefix = os.environ["PREFIX"]
		print("Prefix loaded from os environment variable: \'{}\'".format(prefix))
	return prefix

def getVersion():
	try:
		with open('config.json', 'r') as file:
			configs = json.load(file)
			version = configs["version"]
			print("Version info loaded from config.json: {}".format(version))
	except IOError as e:
		version = os.environ["VERSION"]
		print("Version info loaded from os environment variable: {}".format(version))
	return version

