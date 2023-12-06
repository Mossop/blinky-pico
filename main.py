import network
import time
import sys
import requests
from machine import Pin
from neopixel import NeoPixel
import _thread

from blinky import CONFIG, Logger, main, parse_animations


class Pixels:
    def __init__(self, machine, count):
        self.machine = machine
        self.count = count
        self.leds = NeoPixel(Pin.board.GP15, count)
        self.fill((0, 0, 0))
        self.write()

    def __getitem__(self, index):
        (g, r, b) = self.leds[index]
        return (r, g, b)

    def __setitem__(self, index, value):
        (r, g, b) = value
        self.leds[index] = (g, r, b)

    def __len__(self):
        return self.count

    def fill(self, pixel):
        (r, g, b) = pixel
        self.leds.fill((g, r, b))

    def write(self):
        self.leds.write()


def pull_animations(url, last_etag = None):
    machine.led.value(True)

    try:
        headers = {}
        if last_etag is not None:
            headers["If-None-Match"] = last_etag
        response = requests.get(url, headers=headers)

        try:
            if response.status_code == 200:
                if "ETag" in response.headers:
                    last_etag = response.headers["ETag"]

                animations = parse_animations(machine, response.json())
                return (animations, last_etag)
        finally:
            response.close()

        return (None, last_etag)
    finally:
        machine.led.value(False)


class PicoMachine:
    animations = []
    running = True

    def __init__(self,):
        self.log = Logger(self)
        self.led = Pin('LED', Pin.OUT)
        self.leds = Pixels(self, CONFIG.leds)
        self.leds.write()

        self.wlan = network.WLAN(network.STA_IF)
        self.led.value(True)
        while True:
            try:
                with self.log.logged("Connecting to Wifi"):
                    self.wlan.active(True)
                    self.wlan.connect(CONFIG.ssid, CONFIG.password)

                    while self.wlan.status() < 3:
                        time.sleep_ms(1000)

                break
            except:
                self.wlan.active(False)
                time.sleep_ms(5000)

    def sleep_ms(self, ms):
        time.sleep_ms(ms)

    def ticks(self):
        return time.ticks_ms()

    def ticks_diff(self, a, b):
        return time.ticks_diff(a, b)

    def print_exception(self, exc):
        sys.print_exception(exc)

    def pull_animations(self):
        animations = self.animations
        self.animations = None
        return animations

machine = PicoMachine()
led = Pin('LED', Pin.OUT)
led.value(True)
(animations, last_etag) = pull_animations(CONFIG.config)
machine.animations = animations


def poll_animations(url, last_etag):
    while True:
        with machine.log.safe("Polling for new animations"):
            (animations, last_etag) = pull_animations(url, last_etag)
            if animations is not None:
                machine.animations = animations
        time.sleep_ms(30000)


_thread.start_new_thread(main, (machine,))
try:
    poll_animations(CONFIG.config, last_etag)
finally:
    machine.running = False
