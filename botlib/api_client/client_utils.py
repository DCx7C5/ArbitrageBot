import base64
import collections
import decimal
import hashlib
import hmac
import re
from urllib import parse
from datetime import datetime


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


def to_database_time(any_time):
    db_time_fmt = "%Y-%m-%d %H:%M:%S"
    if isinstance(any_time, str):
        if any_time[-1] == "Z":
            dt_object = datetime.strptime(any_time, "%Y-%m-%dT%H:%M:%SZ")
            return dt_object.strftime(db_time_fmt)
    elif isinstance(any_time, float):
        dt_object = datetime.fromtimestamp(any_time)
        return dt_object.strftime(db_time_fmt)
    elif isinstance(any_time, int):
        dt_object = datetime.fromtimestamp(any_time)
        return dt_object.strftime(db_time_fmt)
