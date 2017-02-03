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

from sys import stderr
from traceback import format_tb
from bdb import BdbQuit
from raven import Client as SentryClient

# TODO: make file to generate crontabs and one that crontabs hook into.

class BundledError(Exception): pass

class ErrorHandler(object):
    """ Bundles errors for compacted logging.
    
    Usage:
        error_handler = ErrorHandler()
        for i in range(1024):
            with error_handler:
                do_dangerous_code()
        error_handler.raise_errors()
        
    Usage [with extra log output]:
        error_handler = ErrorHandler("Job Foo")
        for i in range(1024):
            with error_handler(i):
                do_dangerous_code()
        error_handler.raise_errors()
    """
    
    def __init__(self, descriptor=None, data_limit=100):
        self.errors = {}
        self.descriptor = descriptor
        self.data = None
        self.data_limit = data_limit
    
    def __call__(self, data=None):
        self.data = data
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, exec_type, exec_value, traceback):
        # Don't handle keyboard interrupts or debugger quit exceptions
        if isinstance(exec_value, KeyboardInterrupt) or isinstance(exec_value, BdbQuit):
            return False
        # Handle and batch all other errors
        if isinstance(exec_value, Exception):
            traceback = repr(exec_value) + "\n" + str().join(format_tb(traceback))
            if traceback in self.errors:
                self.errors[traceback].append(self.data)
            else:
                self.errors[traceback] = [self.data]
        return True
    
    def __repr__(self):
        output = ""
        if self.descriptor:
            output += "*** %s ***\n" % self.descriptor
        for traceback, errors in self.errors.items():
            output += "===============\n"
            output += "OCCURRED %s TIMES:\n" % len(errors)
            output += traceback
            if any(errors):
                output += "%s\n" % errors[:self.data_limit]
            output += "===============\n"
        return output
    
    def raise_errors(self):
        output = self.__repr__()
        if self.errors:
            stderr.write(output)
            stderr.write("\n\n")
            raise BundledError()
        

class ErrorSentry(ErrorHandler):
    
    def __init__(self, sentry_dsn, descriptor=None, data_limit=100, sentry_client_kwargs=None):
        
        if sentry_client_kwargs:
            self.sentry_client = SentryClient(dsn=sentry_dsn, **sentry_client_kwargs)
        else:
            self.sentry_client = SentryClient(dsn=sentry_dsn)
            
        super(ErrorSentry, self).__init__(descriptor=descriptor, data_limit=data_limit)

    def __exit__(self, exec_type, exec_value, traceback):
        ret = super(ErrorSentry, self).__exit__(exec_type, exec_value, traceback)
        
        if ret and isinstance(exec_value, Exception):
            self.sentry_client.captureException(exc_info=True)
            
        return ret


class NullErrorHandler():
    def __init__(self, *args, **kwargs):
        pass
    
    def __call__(self, data=None):
        return self
    
    def __enter__(self):
        return self
    
    def __exit__(self, exec_type, exec_value, traceback):
        return False
    
    def raise_errors(self):
        pass

null_error_handler = NullErrorHandler()
