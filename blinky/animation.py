import math

from .color import mix_colors

def assert_str(val):
    if not isinstance(val, str):
        raise Exception("'%s' is not an string" % val)

    return val


def assert_int(val):
    if not isinstance(val, int):
        raise Exception("'%s' is not an integer" % val)

    return val


def assert_bool(val):
    if not isinstance(val, bool):
        raise Exception("'%s' is not a boolean" % val)

    return val


def assert_list(val):
    if not isinstance(val, list):
        raise Exception("'%s' is not a list" % val)

    return val


def assert_color(val):
    if not isinstance(val, list) or len(val) != 3:
        raise Exception("'%s' is not a color" % val)

    return (val[0], val[1], val[2])

parsed_controllers = 0


def parse_controller_sizing(controller, data):
    flex = controller.flex
    width = controller.width

    if "flex" in data:
        flex = assert_int(data["flex"])
        width = None
    elif "width" in data:
        width = assert_int(data["width"])
        flex = None

    if width is None and flex is None:
        raise Exception("Controller must include either a width or flex")

    return (width, flex)


class Controller:
    """A generic controller of a set of leds"""

    flex = None
    width = None
    offset = 0

    def __init__(self, data):
        global parsed_controllers
        parsed_controllers += 1

        if "flex" in data:
            self.flex = assert_int(data["flex"])
            self.width = None
        elif "width" in data:
            self.width = assert_int(data["width"])
            self.flex = None

        if self.width is None and self.flex is None:
            raise Exception("Controller must include either a width or flex")

        if "offset" in data:
            self.offset = assert_int(data["offset"])

    def apply(self, machine, leds, offset):
        pass

    @staticmethod
    def parse_controller(data):
        if assert_str(data["type"]) in CONTROLLERS:
            return CONTROLLERS[data["type"]](data)
        else:
            raise Exception("Unknown controller type: '%s'" % data["type"])


class Container(Controller):
    """A container of controllers"""

    key = "container"

    flex = 1
    width = None

    def __init__(self, data):
        super().__init__(data)

        self.controllers = [Controller.parse_controller(d) for d in assert_list(data["controllers"])]

        if "offsetAdjust" in data:
            self.offset_adjust = assert_int(data["offsetAdjust"])
        else:
            self.offset_adjust = 0

    def clone(self):
        clone = Container({})
        clone.flex = self.flex
        clone.width = self.width
        clone.controllers = self.controllers
        return clone

    def apply(self, machine, leds, offset):
        for (controller_leds, controller, controller_offset) in self.leds:
            controller.apply(machine, controller_leds, offset + controller_offset + controller.offset)

    def assign_leds(self, leds):
        leds = leds[:]

        self.leds = []
        total_width = 0
        total_flex = None

        for controller in self.controllers:
            if controller.width is not None:
                total_width += controller.width
            if controller.flex is not None:
                total_flex = total_flex + controller.flex if total_flex is not None else controller.flex

        flex_width = 0
        flex_extra = 0

        if total_flex is not None:
            remains = len(leds) - total_width
            if remains > 0:
                flex_width = math.floor(remains / total_flex)
                flex_extra = remains - (total_flex * flex_width)

        offset = 0

        while len(leds) > 0:
            for controller in self.controllers:
                width = controller.width
                if width is None:
                    width = controller.flex * flex_width + flex_extra
                    flex_extra = 0

                controller_leds = leds[0:width]
                leds = leds[width:]

                if isinstance(controller, Container):
                    controller = controller.clone()
                    controller.assign_leds(controller_leds)

                if len(controller_leds) > 0:
                    self.leds.append((controller_leds, controller, offset))

            offset += self.offset_adjust


class NoopController(Controller):
    key = "noop"
    flex = 1


class CometController(Controller):
    key = "comet"
    flex = 1
    trail = 4
    spacing = 20
    reverse = False

    def __init__(self, data):
        super().__init__(data)
        color = assert_color(data["color"])

        if "trail" in data:
            self.trail = assert_int(data["trail"])

        if "spacing" in data:
            self.spacing = assert_int(data["spacing"])

        if "reverse" in data:
            self.spacing = assert_bool(data["reverse"])

        self.colors = []
        for n in range(self.trail):
            self.colors.append(mix_colors(color, (0, 0, 0), n / self.trail))

        for n in range(self.spacing):
            self.colors.append((0, 0, 0))


    def apply(self, machine, leds, offset):
        color_pos = offset % len(self.colors)
        adjust = 1 if self.reverse else -1
        for n in range(len(leds)):
            machine.leds[leds[n]] = self.colors[color_pos % len(self.colors)]
            color_pos += adjust


class LookupController(Controller):
    def __init__(self, data):
        super().__init__(data)
        self.colors = []

    def apply(self, machine, leds, offset):
        for led in leds:
            machine.leds[led] = self.colors[offset % len(self.colors)]


class ColorsController(LookupController):
    key = "colors"
    flex = 1

    def __init__(self, data):
        super().__init__(data)

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


CONTROLLERS = {
    c.key: c
    for c in [
        Container,
        NoopController,
        ColorsController,
        CometController
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

        self.controller = Container(data)
        self.controller.assign_leds(list(range(len(machine.leds))))

    def run(self):
        self.machine.leds.fill((0, 0, 0))

        last = None

        for n in range(self.duration):
            self.controller.apply(self.machine, None, n)

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
    global parsed_animations, parsed_controllers

    log.trace("Parsed %s animations with %s controllers" % (parsed_animations, parsed_controllers))
    parsed_animations = 0
    parsed_controllers = 0
