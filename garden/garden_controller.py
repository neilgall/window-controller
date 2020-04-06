
import logging
import threading
import time
from queue import Queue, Empty


logger = logging.getLogger("GardenController")
logger.setLevel(logging.DEBUG)
streamHandler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
streamHandler.setFormatter(formatter)
logger.addHandler(streamHandler)


try:
  import RPi.GPIO as gpio

  READY_PIN = 23
  SWITCH_PIN = 17
  LIGHTS_PINS = [14, 15, 24, 25]
  EVENT_ON = "on"
  EVENT_OFF = "off"
  EVENT_EXIT = "exit"
  ON_DELAY = 2.0


  class ControlThread(threading.Thread):
    def __init__(self):
      threading.Thread.__init__(self)

      gpio.setwarnings(False)
      gpio.setmode(gpio.BCM)
      gpio.setup(READY_PIN, gpio.OUT)
      gpio.setup(SWITCH_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
      gpio.output(READY_PIN, gpio.HIGH)

      for pin in LIGHTS_PINS:
        gpio.setup(pin, gpio.OUT)
        gpio.output(pin, gpio.LOW)

      self._queue = Queue()


    def set_lights_state(self, state):
      event = EVENT_ON if state else EVENT_OFF
      logger.debug(f"sending {event} event")
      self._queue.put(event)


    def exit(self):
      logger.debug(f"sending {EVENT_EXIT} event")
      self._queue.put(EVENT_EXIT)
      self.join()

      gpio.output(READY_PIN, gpio.LOW)
      for pin in LIGHTS_PINS:
        gpio.output(pin, gpio.LOW)
      gpio.cleanup()


    def run(self):
      logger.debug("Starting control thread")
      self._switch_state = self._read_switch()
      self._lights_state = False

      while True:
        try:
          event = self._queue.get(block=True, timeout=1)
          if event == EVENT_EXIT:
            logger.debug("exit")
            break

          elif event == EVENT_ON:
            self._lights_on()

          elif event == EVENT_OFF:
            self._lights_off()

        except Empty:
          switch = self._read_switch()
          if switch != self._switch_state:
            self._switch_state = switch
            self._toggle_lights()


    def _lights_on(self):
      for pin in LIGHTS_PINS:
        logger.debug(f"pin {pin} on")
        gpio.output(pin, gpio.HIGH)
        time.sleep(ON_DELAY)
      self._lights_state = True


    def _lights_off(self):
      for pin in LIGHTS_PINS:
        logger.debug(f"pin {pin} off")
        gpio.output(pin, gpio.LOW)
      self._lights_state = False


    def _toggle_lights(self):
      if self._lights_state:
        self._lights_off()
      else:
        self._lights_on()


    def _read_switch(self):
      return gpio.input(SWITCH_PIN) != 0



  class GardenController:

    def __enter__(self):
      self._controller = ControlThread()
      self._controller.start()
      return self


    def __exit__(self, *args):
      self._controller.exit()
      self._controller = None


    def lights_on(self):
      """
      Turn the lights on
      """
      self._controller.set_lights_state(True)


    def lights_off(self):
      """
      Turn the lights off
      """
      self._controller.set_lights_state(False)


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

