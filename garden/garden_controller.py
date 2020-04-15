
import RPi.GPIO as gpio
import logger
import threading
import time
from enum import Enum
from queue import Queue, Empty


_LOG = logger.create("garden_controller", logger.INFO)

_ZONES = {
    'garden-lights': {
        'friendly_name': 'Garden Fairy Lights',
        'description': 'Fairy Lights all around the Garden',
        'control-pins': [14, 15, 24, 25]
    }
}

READY_PIN = 23
SWITCH_PIN = 17
ON_DELAY = 2.0

class Event(Enum):
    ON = "on"
    OFF = "off"
    EXIT = "exit"
    SET_HOOK = "hook"


class ControlThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

        gpio.setwarnings(False)
        gpio.setmode(gpio.BCM)
        gpio.setup(READY_PIN, gpio.OUT)
        gpio.setup(SWITCH_PIN, gpio.IN, pull_up_down=gpio.PUD_UP)
        gpio.output(READY_PIN, gpio.HIGH)

        for zone in _ZONES.values():
            for pin in zone['control-pins']:
                gpio.setup(pin, gpio.OUT)
                gpio.output(pin, gpio.LOW)

        self._queue = Queue()


    @logger.log_with(_LOG)
    def set_update_hook(self, zone, hook):
        self._queue.put((Event.SET_HOOK, zone, hook))


    @logger.log_with(_LOG)
    def set_lights_state(self, zone, state):
        event = Event.ON if state else Event.OFF
        self._queue.put((event, zone))


    @logger.log_with(_LOG)
    def exit(self):
        self._queue.put((Event.EXIT,))
        self.join()

        gpio.output(READY_PIN, gpio.LOW)
        for zone in _ZONES.values():
          for pin in zone['control-pins']:
            gpio.output(pin, gpio.LOW)
        gpio.cleanup()


    def run(self):
        _LOG.debug("Starting control thread")
        self._switch_state = self._read_switch()
        self._lights_state = { zone: False for zone in _ZONES.keys() }
        self._update_hooks = { zone: None for zone in _ZONES.keys() }

        while True:
            try:
                event, *args = self._queue.get(block=True, timeout=1)
                _LOG.debug(f"handling event {event} {args}")

                if event == Event.EXIT:
                    break

                elif event == Event.ON:
                    self._lights_on(args[0])

                elif event == Event.OFF:
                    self._lights_off(args[0])

                elif event == Event.SET_HOOK:
                    self._update_hooks[args[0]] = args[1]

                else:
                    _LOG.error(f"unknown event {event} for {args}")

            except Empty:
                switch = self._read_switch()
                if switch != self._switch_state:
                  self._switch_state = switch
                  self._toggle_lights(_ZONES.keys()[0])

            except Exception as e:
                _LOG.error(f"unable to process event {event} for {args}: {e}")


    @logger.log_with(_LOG)
    def _lights_on(self, zone):
        if not self._lights_state[zone]:
            self._invoke_hook(zone, True)
            self._lights_state[zone] = True
            for pin in _ZONES[zone]['control-pins']:
                _LOG.debug(f"pin {pin} on")
                gpio.output(pin, gpio.HIGH)
                time.sleep(ON_DELAY)


    @logger.log_with(_LOG)
    def _lights_off(self, zone):
        if self._lights_state[zone]:
            self._invoke_hook(zone, False)
            self._lights_state[zone] = False
            for pin in _ZONES[zone]['control-pins']:
                _LOG.debug(f"pin {pin} off")
                gpio.output(pin, gpio.LOW)


    @logger.log_with(_LOG)
    def _toggle_lights(self, zone):
        if self._lights_state[zone]:
            self._lights_off(zone)
        else:
            self._lights_on(zone)


    @logger.log_with(_LOG)
    def _invoke_hook(self, zone, state):
        hook = self._update_hooks[zone]
        if hook is not None:
            hook(state)


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


    def get_zones(self):
        return _ZONES


    def set_update_hook(self, zone, hook):
        self._controller.set_update_hook(zone, hook)


    def lights_on(self, zone):
        self._controller.set_lights_state(zone, True)


    def lights_off(self, zone):
        self._controller.set_lights_state(zone, False)


if __name__ == "__main__":
    with GardenController():
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass

