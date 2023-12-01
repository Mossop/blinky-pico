def assert_int(val):
    if not isinstance(val, int):
        raise Exception("'%s' is not an integer" % val)

    return val


def assert_list(val):
    if not isinstance(val, list):
        raise Exception("'%s' is not a list" % val)

    return val


def assert_color(val):
    if not isinstance(val, list) or len(val) != 3:
        raise Exception("'%s' is not a color" % val)

    return (val[0], val[1], val[2])


def mix_colors(a, b, offset):
    def mix_val(a, b, offset):
        return int(a + ((b - a) * offset))

    if offset <= 0:
        return a
    if offset >= 1:
        return b

    return (
        mix_val(a[0], b[0], offset),
        mix_val(a[1], b[1], offset),
        mix_val(a[2], b[2], offset),
    )


class Pattern:
    @classmethod
    def parse(cls, animation, data):
        if data["type"] in PATTERNS:
            return PATTERNS[data["type"]](animation, data)

        raise Exception("Unknown pattern: '%s'" % data["type"])

    @property
    def machine(self):
        return self.animation.machine

    def __init__(self, animation, data):
        self.animation = animation

        self.led_specs = []
        def add_led(index, offset):
            if index >= 0 and index < len(self.machine.leds):
                self.led_specs.append((index, offset % animation.duration))

        if "leds" not in data:
            for i in range(len(self.machine.leds)):
                add_led(i, 0)
            return

        def parse_led_spec(spec):
            if isinstance(spec, int):
                self.led_specs.append((spec, 0))
                return

            offset = 0
            if "offset" in spec:
                offset = assert_int(spec["offset"])

            offset_adjust = 0
            if "offsetAdjust" in spec:
                offset_adjust = assert_int(spec["offsetAdjust"])

            repeat = None
            if "repeat" in spec:
                repeat = assert_int(spec["repeat"])

            if "index" in spec:
                index = assert_int(spec["index"])

                if repeat is not None:
                    while index < len(self.machine.leds):
                        add_led(index, offset)
                        index += repeat
                else:
                    add_led(index, offset)

                return

            if "start" in spec:
                start = assert_int(spec["start"])

                length = 1
                if "length" in spec:
                    length = assert_int(spec["length"])

                skip = 0
                if "skip" in spec:
                    skip = assert_int(spec["skip"])

                while start < len(self.machine.leds) and (repeat is None or repeat >= 0):
                    for n in range(length):
                        add_led(start + n, offset)

                    start += length + skip
                    offset += offset_adjust

                    if repeat is not None:
                        repeat -= 1

                return

            raise Exception("Unknown led specification")

        if isinstance(data["leds"], list):
            for led_spec in data["leds"]:
                parse_led_spec(led_spec)
        else:
            parse_led_spec(data["leds"])


    def leds(self, offset):
        for (led, led_offset) in self.led_specs:
            yield (led, (led_offset + offset) % self.animation.duration)

    def init(self):
        pass


class LookupPattern(Pattern):
    def __init__(self, animation, data):
        Pattern.__init__(self, animation, data)
        self.colors = []

    def apply(self, offset):
        for (led, led_offset) in self.leds(offset):
            self.machine.leds[led] = self.colors[led_offset % len(self.colors)]


class Colors(LookupPattern):
    @classmethod
    def key(cls):
        return "colors"

    def __init__(self, animation, data):
        LookupPattern.__init__(self, animation, data)

        default_duration = 0
        default_fade = 0

        if "duration" in data:
            default_duration = assert_int(data["duration"])
        if "fade" in data:
            default_fade = assert_int(data["fade"])

        color_specs = assert_list(data["colors"])

        for n in range(len(color_specs)):
            color_spec = color_specs[n]
            next_color_spec = color_specs[(n + 1) % len(color_specs)]

            duration = default_duration
            fade = default_fade

            if isinstance(color_spec, list):
                color = assert_color(color_spec)
            else:
                color = assert_color(color_spec["color"])
                if "duration" in color_spec:
                    duration = assert_int(color_spec["duration"])
                if "fade" in color_spec:
                    fade = assert_int(color_spec["fade"])

            if isinstance(next_color_spec, list):
                next_color = assert_color(next_color_spec)
            else:
                next_color = assert_color(next_color_spec["color"])

            for n in range(duration):
                self.colors.append(color)

            for n in range(fade):
                mixed = mix_colors(color, next_color, n / fade)
                self.colors.append(mixed)


PATTERNS = {
    p.key(): p
    for p in [
        Colors
    ]
}


class Animation:
    def __init__(self, machine, data):
        self.machine = machine
        self.interval = assert_int(data["interval"])
        self.duration = assert_int(data["duration"])

        self.patterns = [Pattern.parse(self, p) for p in data["patterns"]]

    def run(self):
        self.machine.leds.fill((0, 0, 0))

        for pattern in self.patterns:
            pattern.init()

        for n in range(self.duration):
            for pattern in self.patterns:
                pattern.apply(n)
            self.machine.leds.write()

            self.machine.sleep_ms(self.interval)
