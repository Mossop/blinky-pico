from time import sleep

from .log import Logger
from .config import CONFIG
from .animation import Animation, log_counts

def main(machine, loops = 0):
    count = 0
    animations = None

    while count < loops or loops == 0:
        with machine.log.safe("Updating animations"):
            new_animations = machine.pull_animations()
            if new_animations is not None:
                animations = [Animation(machine, d) for d in new_animations]
                log_counts(machine.log)

        if animations is not None:
            for n in range(len(animations)):
                with machine.log.safe("Running animation %s" % n):
                    animations[n].run()
        else:
            sleep(30)

        if loops > 0:
            count += 1
