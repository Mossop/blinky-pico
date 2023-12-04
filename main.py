import network
import time
import sys
import requests
from machine import Pin
from neopixel import NeoPixel

from blinky import CONFIG, Logger, main


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


class PicoMachine:
    def __init__(self):
        self.log = Logger(self)
        self.led = Pin('LED', Pin.OUT)
        self.leds = Pixels(self, CONFIG.leds)
        self.leds.write()
        self.last_etag = None

        self.wlan = network.WLAN(network.STA_IF)
        self.led.value(True)
        while True:
            try:
                with self.log.logged("Connecting to Wifi"):
                    self.wlan.active(True)
                    self.wlan.connect(CONFIG.ssid, CONFIG.password)

                    while self.wlan.status() < 3:
                        time.sleep_ms(1000)

                return
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
        self.led.value(True)

        try:
            headers = {}
            if self.last_etag is not None:
                headers["If-None-Match"] = self.last_etag
            response = requests.get(CONFIG.config, headers=headers)

            try:
                if response.status_code == 200:
                    if "ETag" in response.headers:
                        self.last_etag = response.headers["ETag"]

                    return response.json()
            finally:
                response.close()

            return None
        finally:
            self.led.value(False)


main(PicoMachine())
