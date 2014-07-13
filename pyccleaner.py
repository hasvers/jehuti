import os


for path in ("./","./graphview/"):
    for f in os.listdir(path):
        if '.pyc' in f or '~' in f:
        	os.remove(path+f)
