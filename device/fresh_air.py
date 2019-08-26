
import time, sys
import RPi.GPIO as gpio

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

  def __exit__(self, *args):
    gpio.cleanup()

  def push_button(self, pin):
    gpio.output(pin, gpio.HIGH)
    time.sleep(0.5)
    gpio.output(pin, gpio.LOW)

  def open_windows(self):
    push_button(OPEN_WINDOWS_PIN)

  def close_windows(self):
    push_button(CLOSE_WINDOWS_PIN)

