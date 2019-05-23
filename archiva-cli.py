import archiva
import argparse
import os
import json

def get_args():
	parser = argparse.ArgumentParser()
	parser.add_argument("-V", "--verbose-level",
		help="set verbose level: e(rror)|[w(arning)]|i(nfo)|s(uppress)",
		choices=["e", "w", "i", "s"],
		default="w")
	parser.add_argument("-H", "--host",
		help="archiva host (should include protocol)",
		required=True)
	parser.add_argument("-R", "--set-referer",
		help="set Referer header (<host>)",
		action="store_true")
	parser.add_argument("-u", "--user",
		help="archiva user (default=guest), also taken from $ARCHIVA_USR",
		default="guest")
	parser.add_argument("-p", "--password",
		help="archiva password (default=), also taken from $ARCHIVA_PWD",
		default="")

	args = parser.parse_args()

	if args.user == "guest":
		args.user = os.getenv("ARCHIVA_USR", "guest")
	if args.password == "":
		args.password = os.getenv("ARCHIVA_PWD", "")

	return args

if __name__ == "__main__":
	args = get_args()
	logger = archiva.Logger(args.verbose_level)

	try:
		s = archiva.Session(args.host,
			args.user, args.password,
			set_referer=args.set_referer, logger=logger)
		with s:
			vlist = s.get_versions_list("com.xompass.edge", "Printer")
			logger.i(vlist)
	except json.decoder.JSONDecodeError as e:
		logger.e(f"could not decode: {e.doc}")
	except archiva.ErrorResponse as e:
		logger.e(e)

