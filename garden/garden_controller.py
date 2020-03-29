import logging

logger = logging.getLogger("GardenController")
logger.setLevel(logging.INFO)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)

try:
  import RPi.GPIO as gpio

  READY_PIN = 23
  LIGHTS_PIN = 17
  SWITCH_PIN = 24

  class GardenController:
    def __init__(self):
      self._switch_state = False
      self._lights_state = False


    def __enter__(self):
      gpio.setwarnings(False)
      gpio.setmode(gpio.BCM)
      gpio.setup(READY_PIN, gpio.OUT)
      gpio.setup(LIGHTS_PIN, gpio.OUT)
      gpio.setup(SWITCH_PIN, gpio.IN)
      gpio.output(READY_PIN, gpio.HIGH)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      self._switch_state = self.read_switch()
      return self


    def __exit__(self, *args):
      gpio.output(READY_PIN, gpio.LOW)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      gpio.cleanup()


    def read_switch(self):
      """
      Read the current switch state
      """
      return gpio.input(SWITCH_PIN)


    def poll_switch(self):
      """
      Poll the switch state and toggle the lights when it changes
      """
      switch = self.read_switch()
      if switch != self._switch_state:
        self._switch_state = switch
        if self._lights_state:
          self.lights_off()
        else:
          self.lights_on


    def lights_on(self):
      """
      Turn the lights on
      """
      gpio.output(LIGHTS_PIN, gpio.HIGH)
      self._lights_state = True


    def lights_off(self):
      """
      Turn the lights off
      """
      gpio.output(LIGHTS_PIN, gpio.LOW)
      self._lights_state = False


except:
  class GardenController:
    def __enter__(self):
      logger.info("no RPi hardware found; using dev GardenController")
      return self

    def __exit__(self, *args):
      pass


    def poll_switch(self):
      pass


    def lights_on(self):
      logger.info("on")


    def lights_off(self):
      logger.info("off")
