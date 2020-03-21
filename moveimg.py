import shutil
import os
import requests

def getimg(url, filename):
	r = requests.get(url, stream = True)
	with open(filename, 'wb') as output:
		shutil.copyfileobj(r.raw, output) #download the image and save it
		shutil.move("{}".format(filename), "img/{}".format(filename)) #move the file to destination
	for image in os.listdir("img/"):
		if image.endswith(".jpg") or image.endswith(".JPG") or image.endswith(".png") or image.endswith(".PNG") or image.endswith(".gif") or image.endswith(".GIF"):
			return(image)