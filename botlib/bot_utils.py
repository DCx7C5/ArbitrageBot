import threading

from botlib.storage import Storage


class Cached(Storage):
    """Memoization class for caching values incl. storage modifications"""

    def __init__(self, function):
        self.__function = function
        self.__lock = threading.Lock()

    def __call__(self, *args, **kwargs):
        key = str(args) + str(kwargs)
        if key in self.keys():
            with self.__lock:
                return self[key]

        value = self.__function(*args, **kwargs)
        with self.__lock:
            self[key] = value
            return value


class Synchronized:

    def __init__(self):
        self.__lock = threading.Lock()




def retry(decorator):

    def