import os
import json
'''
This module retrieves the essentials for the bot to run, including the token, command prefix and version information
'''
version = ''


def getToken():
    try:
        with open('config.json', 'r') as file:
            configs = json.load(file)
            token = configs["token"]
            print("Token loaded from config.json: {}".format(token))
    except IOError as e:
        token = os.environ["TOKEN"]
        print("Token loaded from os environment variable: {}".format(token))
    except KeyError as e:
        print('config.json not found or OS Environment Variable not found [Token].')
    return token


def getDefaultPrefix():
    try:
        with open('config.json', 'r') as file:  # load the default
            configs = json.load(file)
            prefix = configs["prefix"]
            # print("Default prefix loaded from config.json: \'{}\'".format(prefix))
    except IOError as e:
        prefix = os.environ["PREFIX"]
        print("Prefix loaded from os environment variable: \'{}\'".format(prefix))
    except KeyError as e:
        print('config file or OS Environment Variable not found [Prefix]. Using default prefix(".")')
        prefix = '.'
    return prefix


def getVersion():  # it was stupid to store version info in config files...
    return version


def getBackstage():
    try:
        with open('config.json', 'r') as file:
            configs = json.load(file)
            backstage = configs["backstage_id"]
            print("Backstage channel loaded from config.json: {}".format(backstage))
    except IOError as e:
        backstage = os.environ["BACKSTAGE"]
        print("Version info loaded from os environment variable: {}".format(backstage))
    return backstage


def getPortal():
    try:
        with open('config.json', 'r') as file:
            configs = json.load(file)
            portal = configs["portal_id"]
            print("Portal channel loaded from config.json: {}".format(portal))
    except IOError as e:
        portal = os.environ["PORTAL"]
        print("Portal channel loaded from os environment variable: {}".format(portal))
    return portal


def getErrChannel():
    try:
        with open('config.json', 'r') as file:
            configs = json.load(file)
            portal = configs["error_collecting_id"]
            print("Error collecting channel loaded from config.json: {}".format(portal))
    except IOError as e:
        pass
    return portal
