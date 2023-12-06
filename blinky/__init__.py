from time import sleep

from .log import Logger
from .config import CONFIG
from .animation import Animation, log_counts

def parse_animations(machine, json):
    parsed = [Animation(machine, d) for d in json]
    log_counts(machine.log)
    return parsed

def main(machine):
    animations = None
    animation_index = 0

    while machine.running:
        with machine.log.safe("Updating animations"):
            new_animations = machine.pull_animations()
            if new_animations is not None:
                animations = new_animations
                animation_index = 0

        if animations is not None:
            animation = animations[animation_index]
            with machine.log.safe("Running animation %s" % animation_index):
                animation.run()

            animation_index = (animation_index + 1) % len(animations)
        else:
            sleep(30)

    machine.leds.fill((0, 0, 0))
    machine.leds.write()
