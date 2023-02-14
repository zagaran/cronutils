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

On ubuntu, one can use the following set of installs:
```
sudo apt-get install sendmail mailutils moreutils
```

# Project Setup

To use this project, put a file called cron.py at the top level of your project:

```python
from sys import argv
from cronutils import run_tasks

FIVE_MINUTES = "five_minutes"
HOURLY = "hourly"
FOUR_HOURLY = "four_hourly"
DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"

TASKS = {
    FIVE_MINUTES: [],
    HOURLY: [],
    FOUR_HOURLY: [],
    DAILY: [],
    WEEKLY: [],
    MONTHLY: [],
}

TIME_LIMITS = {
    FIVE_MINUTES: 180, # 3 minutes
    HOURLY: 3600,      # 60 minutes
    FOUR_HOURLY: 5400, # 1.5 hours
    DAILY: 43200,      # 12 hours
    WEEKLY: 86400,     # 1 day
    MONTHLY: 259200,   # 3 days
}


if __name__ == "__main__":
    if len(argv) <= 1:
        raise Exception("Not enough arguments to cron\n")
    elif argv[1] in TASKS:
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
15 0 * * * : daily; cd $PROJECT_PATH; chronic python cron.py daily
0 2 * * 0 : weekly; cd $PROJECT_PATH; chronic python cron.py weekly
15 1 1 * * : monthly; cd $PROJECT_PATH; chronic python cron.py monthly
```

NOTE: if you don't want error emails, remove the `MAILTO` line from your config

NOTE: The above config only works if you are using Vixie cron (the default on
ubuntu/debain).  If you are on a different version of cron, replace
each instance of `$PROJECT_PATH` with the actual project path rather than setting
the variable at the top

For any functions you want to run, import them in cron.py and put the function
name in the appropriate list.  For example, to run the functions `backup_database`
and `send_server_info` daily, you would do:

```python
from package.path import backup_database
from other_package.path import send_server_info

...

TASKS = {
    FIVE_MINUTES: [],
    HOURLY: [],
    FOUR_HOURLY: [],
    DAILY: [backup_database, send_server_info],
    WEEKLY: [],
    MONTHLY: [],
}

...
```
# Kill Times

The time limit of tasks specified in TIME_LIMITS is for emailing you about tasks that take longer than expected to run.
If a task takes over four times the time limit (see MAX_TIME_MULTIPLIER), the process of that task is killed. You can
specify your own custom kill time by passing in param `kill_time` to `run_tasks`. For example, here is an alternate
`cron.py` that specifies custom kill times:

```python
from sys import argv
from cronutils import run_tasks

FIVE_MINUTES = "five_minutes"
HOURLY = "hourly"
FOUR_HOURLY = "four_hourly"
DAILY = "daily"
WEEKLY = "weekly"
MONTHLY = "monthly"

TASKS = {
    FIVE_MINUTES: [],
    HOURLY: [],
    FOUR_HOURLY: [],
    DAILY: [],
    WEEKLY: [],
    MONTHLY: [],
}

TIME_LIMITS = {
    FIVE_MINUTES: 180, # 3 minutes
    HOURLY: 3600,      # 60 minutes
    FOUR_HOURLY: 5400, # 1.5 hours
    DAILY: 43200,      # 12 hours
    WEEKLY: 86400,     # 1 day
    MONTHLY: 259200,   # 3 days
}

KILL_TIMES = {
    FIVE_MINUTES: 300, # 5 minutes
    HOURLY: 3600, # 1 hour
}


if __name__ == "__main__":
    if len(argv) <= 1:
        raise Exception("Not enough arguments to cron\n")
    elif argv[1] in TASKS:
        cron_type = argv[1]
        run_tasks(TASKS[cron_type], TIME_LIMITS[cron_type], cron_type, KILL_TIMES.get(cron_type))
    else:
        raise Exception("Invalid argument to cron\n")
```




# Error Aggregation

Then, within any task you want cron to run on, you can get batched error reports
using the error handler like so:

```python
from cronutils import ErrorHandler

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
OCCURRED 924 TIMES:
IndexError('list index out of range',)
  File "some_file.py", line 3, in some_daily_task
    do_dangerous_code()
  File "some_file.py", line 5, in do_dangerous_code
    some_list[i]
===============
```

# Sentry Integration

To have `run_tasks` raise exceptions instead of logging to stderr, pass the argument
`use_stdio=False`.  Here is a full example:

```python
if __name__ == "__main__":
    if len(argv) <= 1:
        raise Exception("Not enough arguments to cron\n")
    elif argv[1] in TASKS:
        cron_type = argv[1]
        run_tasks(TASKS[cron_type], TIME_LIMITS[cron_type], cron_type, KILL_TIMES.get(cron_type), use_stdio=False)
    else:
        raise Exception("Invalid argument to cron\n")
```

The ErrorHandler also integrates with the [Sentry](https://sentry.io/)
error management service.  You can access this by importing ErrorSentry and using
it as you would the regular ErrorHandler.  When your code encounters an error 
ErrorSentry will send a report to your Sentry account. You may provide it the with a
full, valid [Sentry DSN](https://docs.sentry.io/quickstart/#configure-the-dsn) if you have not
configured sentry elsewhere.

If you want to customize the Sentry client you can pass it extra keyword arguments
at instantiation (see example below). You can also access the client directly
if you want to further interact with it, for example by providing additional
[context](https://docs.sentry.io/learn/context/).

```python
from cronutils import ErrorSentry

# Simplest instantiation
error_sentry = ErrorSentry(sentry_dsn=MY_DSN)

# Complex configuration
error_sentry = ErrorSentry(sentry_dsn=MY_DSN,
                           sentry_client_kwargs=SENTRY_CLIENT_KWARGS)

error_sentry.sentry_client.client.user_context({
        'email': request.user.email
    })

```
ErrorSentry also has an optional `sentry_report_limit` parameter that limits the number of times a specific error will
be reported. Note that errors are counted based on their stack trace, under some conditions you will still receive
multiple similar error reports. Error counts are tracked per-ErrorSentry instance.


# Django Integration

The simplest way to integrate with Django is to make a management command for your cron tasks.  For example:

```python
from django.core.management import BaseCommand
from cronutils import run_tasks

class Command(BaseCommand):
    def add_arguments(self, parser):
        cron_type_help = "Which frequency-group of tasks to run"
        parser.add_argument("cron_type", type=str, choices=TASKS.keys(), help=cron_type_help)
    
    def handle(self, *args, **options):
        cron_type = options["cron_type"]
        run_tasks(TASKS[cron_type], TIME_LIMITS[cron_type], cron_type, KILL_TIMES.get(cron_type), use_stdio=False)
```


# Debugging

There is also a debugging mode: the NullErrorHandler.  This class is a drop-in replacement for all usages of the
ErrorHandler and ErrorSentry classes.  What does it do?  Absolutely nothing.  Just change an import as follows
and errors will be raised as if the ErrorHandler or ErrorSentry were not present:

`from cronutils.error_handler import NullErrorHandler as ErrorHandler`

`from cronutils.error_handler import NullErrorHandler as ErrorSentry`


# Breaking Changes From 0.3 to 0.4
With version 0.4.0, `cronutils` has switched the underlying handler for the ErrorSentry class from `raven` to the newer 
`sentry-sdk`. This means that any configuration of the ErrorSentry client via `sentry_client_kwargs` should be refactored
to be passed to `sentry-sdk.init()` rather than initializing `raven`'s `SentryClient`.