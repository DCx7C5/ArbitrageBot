# Copyright (C) 2012 Sebastian Rahlf <basti at redtoad dot de>
#
# This program is release under the MIT License. You can find the full text of
# the license in the LICENSE file.

import os.path
import sys

__version__ = '0.1.1'

def pytest_addoption(parser):
    group = parser.getgroup('pydevd', 'Python remote debug server')
    group._addoption('--pydevd', 
        dest='pydevd', default=None, metavar='IP:PORT', 
        help='connect to a python debug server running on IP:PORT.')
    group._addoption('--pydevd-io',
        dest='pydevd_io', type='choice', default='both',
        choices=['no', 'stderr', 'stdout', 'both'], metavar='type',
        help='redirect io to debug server: both (default)|stderr|stdout|no')
    group._addoption('--pydev-lib',
        dest='pydev_lib', metavar='PATH',
        help='path to pydev library (e.g. Python egg in your PyCharm dir).')
    
def pytest_configure(config):
    socket = config.getvalue('pydevd')
    if socket is not None:
        addr, port = socket.split(':')

        # prepend path to sys.path
        path = config.getvalue('pydev_lib')
        if path:
            sys.path.insert(0, os.path.expandvars(os.path.expanduser(path)))

        redirect = config.getvalue('pydevd_io')
        stdout = redirect in ('both', 'stdout')
        stderr = redirect in ('both', 'stderr')

        try:
            from pydev import pydevd
        except ImportError:
            # Newer pycharm-debug.egg
            import pydevd

        # salvaged from pydev's source:
        # - host: the user may specify another host, if the debug server is not
        #   in the same machine
        # - stdoutToServer: when this is true, the stdout is passed to the debug
        #   server
        # - stderrToServer: when this is true, the stderr is passed to the debug
        #   server so that they are printed in its console and not in this
        #   process console.
        # - port: specifies which port to use for communicating with the server
        #   (note that the server must be started in the same port). @note:
        #   currently it's hard-coded at 5678 in the client
        # - suspend: whether a breakpoint should be emulated as soon as this
        #   function is called.
        # - trace_only_current_thread: determines if only the current thread
        #   will be traced or all future threads will also have the tracing
        #   enabled.
        pydevd.settrace(host=addr, port=int(port), suspend=False, 
            stdoutToServer=stdout, stderrToServer=stderr,
            trace_only_current_thread=False, overwrite_prev_trace=False)

