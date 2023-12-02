from .color import mix_colors

def assert_str(val):
    if not isinstance(val, str):
        raise Exception("'%s' is not an string" % val)

    return val


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


class Pattern:
    def __init__(self, animation, index, pattern_count, offset, data):
        self.animation = animation
        self.index = index
        self.pattern_count = pattern_count
        self.offset = offset

        if assert_str(data["type"]) in PATTERNS:
            self.instance = PATTERNS[data["type"]](self, data["config"] if "config" in data else None)
        else:
            raise Exception("Unknown pattern type: '%s'" % data["type"])

    @property
    def machine(self):
        return self.animation.machine

    def init(self):
        self.instance.init()

    def apply(self, offset):
        self.instance.apply(offset + self.offset)


class PatternInstance:
    def __init__(self, pattern, data):
        self.pattern = pattern

    @property
    def machine(self):
        return self.pattern.animation.machine

    def init(self):
        pass

    def leds(self):
        led = self.pattern.index
        while led < len(self.pattern.animation.machine.leds):
            yield led
            led += self.pattern.pattern_count


class LookupPattern(PatternInstance):
    def __init__(self, pattern, data):
        PatternInstance.__init__(self, pattern, data)
        self.colors = []

    def apply(self, offset):
        for led in self.leds():
            self.machine.leds[led] = self.colors[offset % len(self.colors)]


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

        self.patterns = []

        pattern_count = 0
        for pattern in assert_list(data["patterns"]):
            if "repeat" in pattern:
                pattern_count += assert_int(pattern["repeat"])
            else:
                pattern_count += 1

        index = 0
        for pattern in assert_list(data["patterns"]):
            repeat = 1
            if "repeat" in pattern:
                repeat = assert_int(pattern["repeat"])

            offset_adjust = 0
            if "offsetAdjust" in pattern:
                offset_adjust = assert_int(pattern["offsetAdjust"])

            offset = 0
            if "offset" in pattern:
                offset = assert_int(pattern["offset"])

            for _ in range(repeat):
                self.patterns.append(Pattern(self, index, pattern_count, offset, pattern))
                offset += offset_adjust
                index += 1

    def run(self):
        self.machine.leds.fill((0, 0, 0))

        for pattern in self.patterns:
            pattern.init()

        for n in range(self.duration):
            for pattern in self.patterns:
                pattern.apply(n)
            self.machine.leds.write()

            self.machine.sleep_ms(self.interval)
