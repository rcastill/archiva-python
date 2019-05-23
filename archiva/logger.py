import sys

from datetime import datetime


class Logger:
    """Simple logger supporting 3 log levels: e(rror)|[w(arning)]|i(nfo)"""

    def __init__(self, level="w"):
        """Constructor

        Args:
                level (str): log level; if level is invalid or "w" it is\
                considered as "w" (default). level can also be "s" to suppress\
                any log, excepting a direct call to `Logger.log`
        """

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
        """Base method

        **ALWAYS** logged

        Args:
                tag (str): log tag (usually level)
                msg (str): log message
                file (file): file where log is written (default=stdout)
        """
        print(f"{datetime.now()} [{tag.upper()}] {msg}", file=file)
        file.flush()

    def i(self, msg, file=sys.stdout):
        """Info log

        Only logged if loglevel == "i"

        Args:
                msg (str): log message
                file (file): file where log is written (default=stdout)
        """
        if self.level <= 1:
            self.log("i", msg, file)

    def w(self, msg, file=sys.stderr):
        """Warning log

        Only logged if loglevel == "w|i"

        Args:
                msg (str): log message
                file (file): file where log is written (default=stderr)
        """
        if self.level <= 2:
            self.log("w", msg, file)

    def e(self, msg, file=sys.stderr):
        """Error log

        Only logged if loglevel == "e|w|i"

        Args:
                msg (str): log message
                file (file): file where log is written (default=stderr)
        """
        if self.level <= 3:
            self.log("e", msg, file)
