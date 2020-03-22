import logging

logger = logging.getLogger("WindowController")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


try:
  import RPi.GPIO as gpio
  import time

  OPEN_WINDOWS_PIN = 23
  CLOSE_WINDOWS_PIN = 24

  class WindowController:
    def __enter__(self):
      gpio.setwarnings(False)
      gpio.setmode(gpio.BCM)
      gpio.setup(OPEN_WINDOWS_PIN, gpio.OUT)
      gpio.setup(CLOSE_WINDOWS_PIN, gpio.OUT)
      gpio.output(OPEN_WINDOWS_PIN, gpio.LOW)
      gpio.output(CLOSE_WINDOWS_PIN, gpio.LOW)
      return self

    def __exit__(self, *args):
      gpio.cleanup()

    def push_button(self, pin):
      gpio.output(pin, gpio.HIGH)
      time.sleep(0.5)
      gpio.output(pin, gpio.LOW)

    def open_windows(self):
      self.push_button(OPEN_WINDOWS_PIN)

    def close_windows(self):
      self.push_button(CLOSE_WINDOWS_PIN)


except:
  class WindowController:
    def __enter__(self):
      logger.info("no RPi hardware found; using dev WindowController")
      return self

    def __exit__(self, *args):
      pass

    def open_windows(self):
      logger.info("open")

    def close_windows(self):
      logger.info("close")
