import sys, os
sys.path.append(os.path.dirname(os.path.abspath(__file__))) # This fixes relative imports


def prepApp(app, filesystem):

	class ExampleContainer(filesystem.BaseContainerFileSystem):

		def __init__(self):
			self.map = [
	            {
	                "name": "videos",
	                "fs": filesystem.FolderShareFileSystem("~/Videos/")
	            },
	            {"name": "pics",
	                "fs": filesystem.FolderShareFileSystem("~/Pictures/")
	            },
	            {
	                "type":"folder",
	                "name": "example folder",
	                "contents":[
	                    {
	                        "name": "docs",
	                        "fs": filesystem.FolderShareFileSystem("~/Documents/")
	                    },
	                    {
	                        "name": "recursive folders",
	                        "fs": filesystem.RecursiveFileSystem()
	                    }

	                ]

	            }

	        ]

	app.auth = lambda x, y: True
	app.fs_handler = ExampleContainer()

