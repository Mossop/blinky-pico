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

parsed_patterns = 0
parsed_instances = 0

class Pattern:
    @classmethod
    def parse_pattern(cls, animation, data):
        if assert_str(data["type"]) in PATTERNS:
            return PATTERNS[data["type"]](animation, data["config"] if "config" in data else None)
        else:
            raise Exception("Unknown pattern type: '%s'" % data["type"])

    def __init__(self, animation, index, pattern_count, offset, instance):
        global parsed_patterns
        parsed_patterns += 1
        self.animation = animation
        self.index = index
        self.pattern_count = pattern_count
        self.offset = offset

        self.leds = []
        led = index
        while led < len(animation.machine.leds):
            self.leds.append(led)
            led += pattern_count

        self.instance = instance

    @property
    def machine(self):
        return self.animation.machine

    def apply(self, offset):
        self.instance.apply(self, offset + self.offset)


class PatternInstance:
    def __init__(self, animation, data):
        global parsed_instances
        parsed_instances += 1
        self.animation = animation

    @property
    def machine(self):
        return self.animation.machine

    def init(self):
        pass


class LookupPattern(PatternInstance):
    def __init__(self, animation, data):
        PatternInstance.__init__(self, animation, data)
        self.colors = []

    def apply(self, pattern, offset):
        for led in pattern.leds:
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

parsed_animations = 0


class Animation:
    def __init__(self, machine, data):
        global parsed_animations
        parsed_animations += 1
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
            instance = Pattern.parse_pattern(self, pattern)

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
                self.patterns.append(Pattern(self, index, pattern_count, offset, instance))
                offset += offset_adjust
                index += 1

    def run(self):
        self.machine.leds.fill((0, 0, 0))

        last = None

        for n in range(self.duration):
            for pattern in self.patterns:
                pattern.apply(n)

            if n > 0:
                now = self.machine.ticks()
                time_spent = self.machine.ticks_diff(now, last)
                if time_spent > self.interval:
                    self.machine.log.warn("Patterns took too long to apply (%sms over)" % (time_spent - self.interval))
                    last = now
                else:
                    self.machine.sleep_ms(self.interval - time_spent)
                    last = self.machine.ticks()
            else:
                last = self.machine.ticks()

            self.machine.leds.write()


def log_counts(log):
    global parsed_animations, parsed_patterns, parsed_instances

    log.trace("Parsed %s animations with %s patterns and %s pattern instances" % (parsed_animations, parsed_patterns, parsed_instances))
    parsed_animations = 0
    parsed_patterns = 0
    parsed_instances = 0
