from urllib import request
import json
import time
from traceback import print_exception

from blinky import CONFIG, main, Logger, parse_animations


class Pixels:
    def __init__(self, machine, count):
        self.machine = machine
        self.leds = []
        for _ in range(count):
            self.leds.append((255, 0, 0))

    def __getitem__(self, index):
        return self.leds[index]

    def __setitem__(self, index, value):
        self.leds[index] = value

    def __len__(self):
        return len(self.leds)

    def fill(self, pixel):
        for n in range(len(self.leds)):
            self.leds[n] = pixel

    def write(self):
        for color in self.leds:
            print("\x1b[38;2;%s;%s;%sm*\x1b[0m" % color, end="")
        print("")


class DesktopMachine:
    running = True

    def __init__(self):
        self.leds = Pixels(self, CONFIG.leds)
        self.log = Logger(self)
        self.last_data = None

    def sleep_ms(self, ms):
        time.sleep(ms / 1000)

    def ticks(self):
        return time.monotonic_ns()

    def ticks_diff(self, a, b):
        return int((a - b) / 1000000)

    def print_exception(self, exc):
        print_exception(exc)

    def pull_animations(self):
        with request.urlopen(CONFIG.config) as response:
            data = response.read()
            if self.last_data == data:
                return None

            self.last_data = data
            return parse_animations(self, json.loads(data))


main(DesktopMachine())
