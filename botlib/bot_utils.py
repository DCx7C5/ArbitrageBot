import time
import threading
from botlib.storage import Storage
from botlib.bot_log import api_logger


def repeat_call(num_repeats):
    """
    Decorator function for handling errors in important API calls
    """
    def _decorator(function):
        # noinspection PyBroadException
        def __wrapper(*args):
            counter = 0
            exchange = args[0]
            try:
                refid = args[1]
            except:
                refid = None
            while counter < num_repeats + 1:
                try:
                    return function(*args)
                except:
                    counter += 1
                    api_logger.critical(f"Failed to call {function.__name__} on {exchange} for {refid} {counter} times")
                    if counter < num_repeats:
                        time.sleep(counter)
        return __wrapper
    return _decorator


class Cached(Storage):
    """Memoization class for caching values incl. storage modifications"""

    def __init__(self, function):
        self.__function = function
        self.__lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        key = str(args) + str(kwargs)
        if key in self.__dict__:
            print("Returned from Cache")
            with self.__lock:
                return self[key]

        value = self.__function(*args, **kwargs)
        with self.__lock:
            print("Returned from function call")
            self[key] = value
            return value
