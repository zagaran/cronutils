Cronutils
========

This tool is designed to simplify the configuration and dispatching of tasks via
cron, as well as to give nicely formatted error reports by email.

It can be installed by pip:

```
pip install cronutils
```

For the email error reporting to work properly, this project depends on cronic:
http://habilis.net/cronic/


# Project Setup

To use this project, put a file called cron.py at the top level of your project:

```
from sys import argv
from cronutils.task_runner import run_tasks

FIVE_MINUTES = "five_minutes"
HOURLY = "hourly"
FOUR_HOURLY = "four_hourly"
DAILY = "daily"
WEEKLY = "weekly"

TASKS = {
    FIVE_MINUTES: [],
    HOURLY: [],
    FOUR_HOURLY: [],
    DAILY: [],
    WEEKLY: []
}

TIME_LIMITS = {
    FIVE_MINUTES: 180, # 3 minutes
    HOURLY: 3600,      # 60 minutes
    FOUR_HOURLY: 5400, # 1.5 hours
    DAILY: 43200,      # 12 hours
    WEEKLY: 86400,     # 1 day
}

VALID_ARGS = [FIVE_MINUTES, HOURLY, FOUR_HOURLY, DAILY, WEEKLY]


if __name__ == "__main__":
    if len(argv) <= 1:
        raise Exception("Not enough arguments to cron\n")
    elif argv[1] in VALID_ARGS:
        cron_type = argv[1]
        run_tasks(TASKS[cron_type], TIME_LIMITS[cron_type], cron_type)
    else:
        raise Exception("Invalid argument to cron\n")
```


Then, add the following to your cron config, modifying `MAILTO` and
`PROJECT_PATH` appropriately:

```
PROJECT_PATH="/path/to/project_name"
MAILTO="user@example.com,user2@example.com"
# m h  dom mon dow   command
*/5 * * * * : five_minutes; cd $PROJECT_PATH; chronic python cron.py five_minutes
0 */1 * * * : hourly; cd $PROJECT_PATH; chronic python cron.py hourly
30 */4 * * * : four_hourly; cd $PROJECT_PATH; chronic python cron.py four_hourly
@daily : daily; cd $PROJECT_PATH; chronic python cron.py daily
0 2 * * 0 : weekly; cd $PROJECT_PATH; chronic python cron.py weekly
```

NOTE: if you don't want error emails, remove the `MAILTO` line from your config

NOTE: The above config only works if you are using Vixie cron (the default on
ubuntu/debain).  If you are on a different version of cron, replace
each instance of `$PROJECT_PATH` with the actual project path rather than setting
the variable at the top

For any functions you want to run, import them in cron.py and put the function
name in the appropriate list.  For example, to run the functions `backup_database`
and `send_server_info` daily, you would do:

```
from package.path import backup_database
from other_package.path import send_server_info

...

TASKS = {
    FIVE_MINUTES: [],
    HOURLY: [],
    FOUR_HOURLY: [],
    DAILY: [backup_database, send_server_info],
    WEEKLY: []
}

...
```

# Error Aggregation

Then, within any task you want cron to run on, you can get batched error reports
using the error handler like so:

```
from cronutils.error_hanlder import ErrorHandler

def some_daily_task():
    error_handler = ErrorHandler()
    for i in range(1024):
        with error_handler:
            do_dangerous_code()
    error_handler.raise_errors()
```

Any errors generated in the with block will be aggregated by stacktrace, so if
there are errors, you will get a report that looks like this:

```
===============
OCCURED 924 TIMES:
IndexError('list index out of range',)
  File "some_file.py", line 3, in some_daily_task
    do_dangerous_code()
  File "some_file.py", line 5, in do_dangerous_code
    some_list[i]
===============
```
