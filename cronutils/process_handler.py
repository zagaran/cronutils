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
    start_time = None
    end_time = None
    _killed = False
    _stopped = False

    def __init__(self, function):
        self.name = function.__name__
        self.function = function
        self.process = Process(target=_run_task, args=(function,))

    def start(self):
        self.start_time = default_timer()
        self.process.start()

    def stop(self, kill=False):
        if self._stopped:
            raise Exception('already stopped')
        self.end_time = default_timer()
        self.process.join(0)

        if kill:
            self.process.terminate()
            self._killed = True

        self._stopped = True

    def get_run_time(self):
        return self.end_time - self.start_time

    def get_run_time_message(self):
        extra = " (Killed before finishing)" if self.killed() else ""
        return str(self.get_run_time()) + extra

    def started(self):
        return self.process.pid is not None

    def stopped(self):
        return self._stopped

    def killed(self):
        return self._killed

    def running(self):
        return self.process.is_alive()

    def finished(self):
        return self.process.pid and not self.process.is_alive()
