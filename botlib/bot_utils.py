import base64
import collections
import decimal
import hashlib
import hmac
import re
import time
import threading
from urllib import parse

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


def generate_path_from_params(params, endpoint):
    params_string = "?"
    for p in params:
        params_string += f'{p}={params[p]}' + "&"
    return f'{endpoint}{params_string[:-1]}'


def precision_from_string(string):
    parts = re.sub(r'0+$', '', string).split('.')
    return len(parts[1]) if len(parts) > 1 else 0


def number_to_string(x):
    d = decimal.Decimal(str(x))
    return '{:f}'.format(d)


def implode_params(string, params):
    if isinstance(params, dict):
        for key in params:
            if not isinstance(params[key], list):
                string = string.replace('{' + key + '}', str(params[key]))
    return string


def hmac_val(request, secret, algorithm=hashlib.sha256, digest='hex'):
    h = hmac.new(secret, request, algorithm)
    if digest == 'hex':
        return h.hexdigest()
    elif digest == 'base64':
        return base64.b64encode(h.digest())
    return h.digest()


def url_encode(params=None):
    if params is None:
        params = {}
    if isinstance(params, dict) or isinstance(params, collections.OrderedDict):
        return parse.urlencode(params)
    return params


def omit(d, *args):
    if isinstance(d, dict):
        result = d.copy()
        for arg in args:
            if type(arg) is list:
                for key in arg:
                    if key in result:
                        del result[key]
            else:
                if arg in result:
                    del result[arg]
        return result
    return d


def extend(*args):
    if args is not None:
        if type(args[0]) is collections.OrderedDict:
            result = collections.OrderedDict()
        else:
            result = {}
        for arg in args:
            result.update(arg)
        return result
    return {}
