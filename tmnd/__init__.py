import logging

__version__ = '0.0.1'

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
logger = logging.getLogger('tmnd')
logger.addHandler(handler)
logger.setLevel('CRITICAL')
