import logging
from logging import ERROR, WARN, INFO, DEBUG


def create(name, level):
  logger = logging.getLogger(name)
  logger.setLevel(level)
  streamHandler = logging.StreamHandler()
  formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
  streamHandler.setFormatter(formatter)
  logger.addHandler(streamHandler)
  return logger

