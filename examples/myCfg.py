
import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


import wco



def prepApp(app, filesystem):
	wco.filesystem=filesystem


	app.auth = lambda x, y: True
	app.fs_handler = wco.WcoFileSystem()

