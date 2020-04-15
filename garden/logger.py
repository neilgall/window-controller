import functools
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


class log_with:
    def __init__(self, logger, **extra_args):
        self._logger = logger
        self._extra_args = extra_args

    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self._logger.debug(f'ENTER {func.__name__} {self._extra_args} {args} {kwargs}')
            result = func(*args, **kwargs)
            self._logger.debug(f'EXIT {func.__name__} {result}')
            return result
        return wrapper