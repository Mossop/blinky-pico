class Logger:
    def __init__(self, machine):
        self.machine = machine

    def _log(self, type, str):
        print("%s: %s" % (type, str))

    def trace(self, *args):
        self._log("TRACE", *args)

    def info(self, *args):
        self._log("INFO", *args)

    def warn(self, *args):
        self._log("WARN", *args)

    def error(self, *args):
        self._log("ERROR", *args)

    def logged(self, message):
        return LoggedBlock(self, message, False)

    def safe(self, message):
        return LoggedBlock(self, message, True)


class LoggedBlock:
    def __init__(self, logger, message, safe):
        self.logger = logger
        self.message = message
        self.safe = safe

    def __enter__(self):
        self.logger.trace(self.message)
        self.start = self.logger.machine.ticks()

    def __exit__(self, exc_type, exc, tb):
        end = self.logger.machine.ticks()
        duration = self.logger.machine.ticks_diff(end, self.start)

        if exc_type is not None:
            if isinstance(exc, KeyboardInterrupt):
                return False

            self.logger.error("%s: Exception in %sms" % (self.message, duration))
            self.logger.machine.print_exception(exc)
        else:
            self.logger.trace("%s: Complete in %sms" % (self.message, duration))
        return self.safe
