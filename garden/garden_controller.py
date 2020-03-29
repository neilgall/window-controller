import logging
import threading
import time

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
  SWITCH_PIN = 22

  class PollThread(threading.Thread):
    def __init__(self, read_state_fn, on_change_fn):
      threading.Thread.__init__(self)
      self._read_state = read_state_fn
      self._on_change = on_change_fn
      self._switch_state = read_state_fn()
      self._stopped = False


    def run(self):
      logger.debug("Starting polling thread")
      while not self._stopped:
        switch = self._read_state()
        logger.debug(f"poll switch state={switch} was={self._switch_state}")
        if switch != self._switch_state:
          self._switch_state = switch
          self._on_change(switch)
        time.sleep(1)


    def stop(self):
      logger.debug("Stopping polling thread")
      self._stopped = True
      self.join()


  class GardenController:
    def __init__(self):
      self._lights_state = False


    def __enter__(self):
      gpio.setwarnings(False)
      gpio.setmode(gpio.BCM)
      gpio.setup(READY_PIN, gpio.OUT)
      gpio.setup(LIGHTS_PIN, gpio.OUT)
      gpio.setup(SWITCH_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
      gpio.output(READY_PIN, gpio.HIGH)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      self._poll_thread = PollThread(self._read_switch, self._toggle_lights)
      self._poll_thread.start()
      return self


    def __exit__(self, *args):
      self._poll_thread.stop()
      gpio.output(READY_PIN, gpio.LOW)
      gpio.output(LIGHTS_PIN, gpio.LOW)
      gpio.cleanup()


    def _read_switch(self):
      """
      Read the current switch state
      """
      return gpio.input(SWITCH_PIN)


    def _toggle_lights(self, switch_state):
      """
      Toggle the lights from their current state
      """
      if self._lights_state:
        self.lights_off()
      else:
        self.lights_on()


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


    def lights_on(self):
      logger.info("on")


    def lights_off(self):
      logger.info("off")


if __name__ == "__main__":
  with GardenController():
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      pass

