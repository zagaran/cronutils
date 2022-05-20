"""
The MIT License (MIT)

Copyright (c) 2014 Zagaran, Inc.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.

@author: Zags (Benjamin Zagorsky)
"""

from sys import exit, stderr
from timeit import default_timer
from time import sleep

from cronutils.process_handler import ProcessHandler

MAX_TIME_MULTIPLIER = 4


class TaskError(Exception): pass


def run_tasks(tasks, time_limit, cron_type, kill_time=None, use_stdio=True, max_tasks=None):
    """
    Runs the tasks, each as their own process.  If any of the tasks take
    longer than time_limit * MAX_TIME_MULTIPLIER, they are terminated.
    If any of the tasks return non-zero status, this function exits with
    status 1 to signify an error to cronic.  Also, if any of the tasks
    take longer than time_limit, the process exits with status 1.
    
    @param tasks: a list of function pointers of the tasks to be run
    @param time_limit: the integer number of seconds to use as the time limit
    @param cron_type: a string representing this cron type; used in error logs
    @param kill_time: a int representing time in seconds when a job is killed if
        it hasn't finished yet; if this is None, run_tasks will use
        time_limit * MAX_TIME_MULTIPLIER as the kill time.
    @param use_stdio: a boolean; if True (the default), errors will be
        written to stderr and success will be written to stdout; if True,
        errors will be raised as an exception and success will be returned
    @param max_tasks: an int; the number of tasks to run simultaneously.
        If None then all tasks run at once.
    """
    # TODO: support no time limit
    # TODO: include error message for tasks that were killed
    if not kill_time:
        kill_time = time_limit * MAX_TIME_MULTIPLIER
    start = default_timer()

    processes = [ProcessHandler(function) for function in tasks]

    # If max_tasks is None, list slicing returns the whole list
    for p in processes[:max_tasks]:
        p.start()

    for _ in range(kill_time):
        if all(p.stopped() for p in processes):
            break

        for p in processes:
            if p.finished() and not p.stopped():
                p.stop()

        # If task counting is enabled
        if max_tasks:
            running_task_count = sum(1 for p in processes if p.running())
            required_new_tasks = max_tasks - running_task_count
            not_started_tasks = [p for p in processes if not p.started()]
            for p in not_started_tasks[:required_new_tasks]:
                p.start()

        sleep(1)

    for p in processes:
        if p.started() and not p.stopped():
            p.stop(kill=True)
    
    total_time = default_timer() - start
    errors = ["Error in running function '%s'\n" % p.name for p in processes if p.process.exitcode]
    
    if total_time > time_limit or total_time > kill_time:
        errors.append("ERROR: cron job: over time limit")

    tasks_left = [p.name for p in processes if not p.started()]
    if tasks_left:
        errors.append("The following tasks never ran: " + ', '.join(tasks_left))

    process_times = {
        p.name: p.get_run_time_message() for p in processes if p.stopped()
    }

    if errors:
        error_message = "Cron type %s completed with errors; total time %s\n" % (cron_type, total_time)
        error_message += "%s\n" % process_times
        for error in errors:
            error_message += error
            error_message += "\n"
        if use_stdio:
            stderr.write(error_message)
            exit(1)
        else:
            raise TaskError(error_message)
    else:
        if use_stdio:
            print("Cron type %s completed; total time %s" % (cron_type, total_time))
            print(str(process_times))
        else:
            return total_time, process_times


def process_finished(process):
    return process.pid and not process.is_alive()
