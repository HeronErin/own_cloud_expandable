





import argparse, os, hashlib, sys


from runpy import run_path





def defaultUserChecker(username, password): # Only works with admin admin
	if username != "admin":
		return False
	if "|" in username:
		return False

	# A half-assed salting approach 
	if hashlib.sha512(f"{username}|{password}".encode("utf-8")).hexdigest() == \
	 "5e4a496569cfbd2350cb1a44ff1d8bae70baaeaaf54e83ac31ed3f96242c7b77500c7ef5fa566cf1bfb4f982a9c9621fa20dada7c2c50a09344707f39d5fde08":
		return True
	return False




if __name__ == "__main__":

	parser = argparse.ArgumentParser(
	                    prog='Better OwnCloud server',
	                    description='By reimplementing most of the OwnCloud protocol, it allows for the easy creating of OwnCloud servers. You can easily share a folder with anybody on the internet, or just your home internet, or create a full customizable media sharing center.',
	                    epilog='https://github.com/HeronErin/')
	parser.add_argument("-H", "--host", help="What ip to host the server on", default="0.0.0.0")


	parser.add_argument("-S", "--share", help="Share a folder")

	parser.add_argument("-C", "--custom", help="Use a python file to prepare the flask app")

	parser.add_argument("-P", "--port", help="What port to host the server on", default=5678, type=int)

	parser.add_argument("-i", "--init", help="Init ssl certs and secret keys", action="store_true")




	parser.add_argument("--no-ssl", help="Disable https", action="store_true")

	args = parser.parse_args()

	# sys.path.append(os.path.dirname(os.path.abspath(__file__))) # This fixes relative imports
	# os.chdir(os.path.dirname(os.path.abspath(__file__)))
	
	from src.flaskServer import *
	from src import filesystem
	

	if args.init:
		os.chwd(os.path.dirname(os.path.abspath(__file__)))
		if os.path.exists("crypto/secret.key"):
			if input("May already be initilized, do you wish to continue (y/n): ") != "y":
				exit()
		print("\n\nYou will be asked some questions, leave EVERYTHING BLANK EXCEPT Common name\n")
		try: os.mkdir("crypto")
		except: pass
		os.system("""cd crypto \
			&& openssl genrsa -out domain.key 4096 \
			&& openssl req -key domain.key -new -out domain.csr \
			&& openssl x509 -signkey domain.key -in domain.csr -req -days 365 -out domain.crt \
			&& openssl rand 32 > secret.key""")


		exit()

	if args.share is not None:

		app.auth = defaultUserChecker
		app.fs_handler = filesystem.FolderShareFileSystem(args.share)

		baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto")
		ssl_context = None if args.no_ssl else (os.path.join(baseDir, "domain.crt"), os.path.join(baseDir, "domain.key"), )

		app.run(host=args.host, port=args.port, ssl_context=ssl_context)
	elif args.custom:

		customizable = run_path(args.custom)
		customizable["prepApp"](app, filesystem)

		baseDir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crypto")
		ssl_context = None if args.no_ssl else (os.path.join(baseDir, "domain.crt"), os.path.join(baseDir, "domain.key"), )

		app.run(host=args.host, port=args.port, ssl_context=ssl_context)