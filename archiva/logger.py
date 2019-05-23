import sys

from datetime import datetime

class Logger:
	def __init__(self, level="w"):
		if level.lower().startswith("i"):
			self.level = 1
		elif level.lower().startswith("w"):
			self.level = 2
		elif level.lower().startswith("s"):
			# suppress
			self.level = 4
		else:
			self.level = 3

	def log(self, tag, msg, file=sys.stdout):
		print(f"{datetime.now()} [{tag.upper()}] {msg}", file=file)
		file.flush()

	def i(self, msg, file=sys.stdout):
		if self.level <= 1:
			self.log("i", msg, file)

	def w(self, msg, file=sys.stderr):
		if self.level <= 2:
			self.log("w", msg, file)

	def e(self, msg, file=sys.stderr):
		if self.level <= 3:
			self.log("e", msg, file)