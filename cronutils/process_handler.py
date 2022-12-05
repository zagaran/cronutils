from multiprocessing import Process
from timeit import default_timer

from cronutils.error_handler import BundledError


def _run_task(function):
    """ Helper function used by run_tasks """
    try:
        function()
    except BundledError:
        exit(1)


class ProcessHandler:
    _start_time = None
    _end_time = None
    _killed = False
    stopped = False

    def __init__(self, function):
        self.name = function.__name__
        self.function = function
        self.process = Process(target=_run_task, args=(function,))

    def start(self):
        self._start_time = default_timer()
        self.process.start()

    def stop(self):
        if self.stopped:
            raise Exception('already stopped')
        self._end_time = default_timer()
        self.process.join(0)
        self.stopped = True

    def kill(self):
        self.stop()
        self.process.terminate()
        self._killed = True

    def check_completed(self):
        if self.finished() and not self.stopped:
            self.stop()

    def get_run_time(self):
        return self._end_time - self._start_time

    def get_run_time_message(self):
        message = str(self.get_run_time())
        if self._killed:
            message += " (Killed before finishing)"
        return message

    def started(self):
        return self.process.pid is not None

    def running(self):
        return self.process.is_alive()

    def finished(self):
        return self.process.pid and not self.process.is_alive()
