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

from multiprocessing import Process
from sys import exit, stderr
from timeit import default_timer
from time import sleep

from cronutils.error_handler import BundledError

MAX_TIME_MULTIPLIER = 4

def run_tasks(tasks, time_limit, cron_type, kill_time=None):
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
    """
    # TODO: support no time limit
    # TODO: include error message for tasks that were killed
    if not kill_time:
        kill_time = time_limit * MAX_TIME_MULTIPLIER
    start = default_timer()
    process_times = {}
    processes = dict((function.__name__, Process(target=_run_task, args=[function]))
                     for function in tasks)
    for p in processes.values():
        p.start()
    for _ in range(kill_time):
        if not any(i.is_alive() for i in processes.values()):
            break
        for name, p in processes.items():
            if not p.is_alive() and name not in process_times:
                process_times[name] = default_timer() - start
                p.join(0)
        sleep(1)
    for name, p in processes.items():
        p.join(0)
        p.terminate()
        if name not in process_times:
            process_times[name] = default_timer() - start
    total_time = default_timer() - start
    errors = ["Error in running function '%s'\n" % name
              for name, p in processes.items() if p.exitcode]
    if total_time > time_limit or total_time > kill_time:
        errors.append("ERROR: cron job: over time limit")
    if errors:
        stderr.write("Cron type %s completed; total time %s\n" % (cron_type, total_time))
        stderr.write("%s\n" % process_times)
        for error in errors:
            stderr.write(error)
        exit(1)
    else:
        print("Cron type %s completed; total time %s" % (cron_type, total_time))
        print(str(process_times))

def _run_task(function):
    """ Helper function used by run_tasks """
    try: function()
    except BundledError: exit(1)
