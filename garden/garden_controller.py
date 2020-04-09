
import logger
import threading
import time
from queue import Queue, Empty


_LOG = logger.create("garden_controller", logger.INFO)

_ZONES = {
  'summerhouse-lights': [24],
  'garden-lights': [14, 15, 25]
}

try:
  import RPi.GPIO as gpio

  READY_PIN = 23
  SWITCH_PIN = 17
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

      for zone_pins in _ZONES.values():
        for pin in zone_pins:
          gpio.setup(pin, gpio.OUT)
          gpio.output(pin, gpio.LOW)

      self._queue = Queue()


    def set_lights_state(self, zone, state):
      event = EVENT_ON if state else EVENT_OFF
      _LOG.debug(f"sending {event} event for zone {zone}")
      self._queue.put((event, zone))


    def exit(self):
      _LOG.debug(f"sending {EVENT_EXIT} event")
      self._queue.put((EVENT_EXIT, None))
      self.join()

      gpio.output(READY_PIN, gpio.LOW)
      for zone_pins in _ZONES.values():
        for pin in zone_pins:
          gpio.output(pin, gpio.LOW)
      gpio.cleanup()


    def run(self):
      _LOG.debug("Starting control thread")
      self._switch_state = self._read_switch()
      self._lights_state = { zone: False for zone in _ZONES.keys() }

      while True:
        try:
          event, zone = self._queue.get(block=True, timeout=1)
          if event == EVENT_EXIT:
            _LOG.debug("exit")
            break

          elif event == EVENT_ON:
            self._lights_on(zone)

          elif event == EVENT_OFF:
            self._lights_off(zone)

          else:
            _LOG.error(f"unknown event {event} for zone {zone}")

        except Empty:
          switch = self._read_switch()
          if switch != self._switch_state:
            self._switch_state = switch
            self._toggle_lights('summerhouse-lights')

        except Exception as e:
          _LOG.error(f"unable to process event {event} for zone {zone}: {e}")


    def _lights_on(self, zone):
      for pin in _ZONES[zone]:
        _LOG.debug(f"pin {pin} on")
        gpio.output(pin, gpio.HIGH)
        time.sleep(ON_DELAY)
      self._lights_state[zone] = True


    def _lights_off(self, zone):
      for pin in _ZONES[zone]:
        _LOG.debug(f"pin {pin} off")
        gpio.output(pin, gpio.LOW)
      self._lights_state[zone] = False


    def _toggle_lights(self, zone):
      if self._lights_state[zone]:
        self._lights_off(zone)
      else:
        self._lights_on(zone)

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


    def lights_on(self, zone):
      self._controller.set_lights_state(zone, True)


    def lights_off(self, zone):
      self._controller.set_lights_state(zone, False)


except:
  class GardenController:
    def __enter__(self):
      _LOG.info("no RPi hardware found; using dev GardenController")
      return self

    def __exit__(self, *args):
      pass


    def lights_on(self, zone):
      _LOG.info(f"{zone} on")


    def lights_off(self, zone):
      _LOG.info(f"{zone} off")


if __name__ == "__main__":
  with GardenController():
    try:
      while True:
        time.sleep(1)
    except KeyboardInterrupt:
      pass

