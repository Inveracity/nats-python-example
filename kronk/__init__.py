import logging
import sys


class StdErrFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.FATAL, logging.ERROR, logging.WARNING)


class StdOutFilter(logging.Filter):
    def filter(self, rec):
        return rec.levelno in (logging.DEBUG, logging.INFO)


logger = logging.getLogger()
logger.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s [%(levelname)-7s] %(message)s')

h1 = logging.StreamHandler(sys.stdout)
h1.setLevel(logging.DEBUG)
h1.setFormatter(formatter)
h1.addFilter(StdOutFilter())


h2 = logging.StreamHandler(sys.stderr)
h2.setLevel(logging.WARNING)
h2.setFormatter(formatter)
h2.addFilter(StdErrFilter())

logger.addHandler(h1)
logger.addHandler(h2)
