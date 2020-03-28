import logging

logger = logging.getLogger("WindowController")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

try:
  import RPi.GPIO as gpio

  READY_PIN = 23
  LIGHTS_PIN = 17

  class WindowController:
    def __enter__(self):
      gpio.setwarnings(False)
      gpio.setmode(gpio.BCM)
      gpio.setup(READY_PIN, gpio.OUT)
      gpio.setup(LIGHTS_PIN, gpio.OUT)
      gpio.output(READY_PIN, gpio.HIGH)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      return self

    def __exit__(self, *args):
      gpio.output(READY_PIN, gpio.LOW)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      gpio.cleanup()

    def lights_on(self):
      gpio.output(LIGHTS_PIN, gpio.HIGH)

    def lights_off(self):
      gpio.output(LIGHTS_PIN, gpio.LOW)


except:
  class GardenController:
    def __enter__(self):
      logger.info("no RPi hardware found; using dev GardenController")
      return self

    def __exit__(self, *args):
      pass

    def lights_on(self):
      logger.info("on")

    def lights_off(self):
      logger.info("off")
