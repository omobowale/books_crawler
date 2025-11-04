import logging


logger = logging.getLogger("books_crawler")
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
ch.setFormatter(fmt)
logger.addHandler(ch)