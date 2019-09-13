import base64
import collections
import decimal
import hashlib
import hmac
import re
from threading import Lock
from urllib import parse
from datetime import datetime

from botlib.storage import Storage


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


class MarketManager(Storage):
    """
    Market management and initialization class

    Attributes:
        all markets on exchange indexed with exchange specific refid
    """
    def __init__(self, api_data, sql_data):
        for market in api_data:
            refid = market['refid']
            self[refid] = Market(refid)
            self[refid].base_asset = market['base_asset']
            self[refid].quote_asset = market['quote_asset']
            self[refid].minimum_order_volume = float(market['minimum_order_volume'])
            self[refid].price_precision = int(market['price_precision'])
            self[refid].order_volume_precision = int(market['order_volume_precision'])
            self[refid].order_volume_step_size = float(market['order_volume_step_size'])
            self[refid].minimum_order_cost = float(market['minimum_order_cost']) if market['minimum_order_cost'] else 0.0000001

            for _market in sql_data:
                if _market['refid'] == refid:
                    self[refid].minimum_profit_rate = float(_market['min_profit'])
                    self[refid].maximum_order_cost = float(_market['max_size'])
                    self[refid].deposit_address = _market['deposit']


class Market(Storage):
    """Market helper class"""
    def __init__(self, refid: str):
        self.refid = refid
        self.__lock = Lock()
        self._base_asset = None
        self._quote_asset = None

        self._price_precision = None
        self._order_volume_step_size = None
        self._minimum_order_volume = None
        self._minimum_order_cost = None
        self._order_volume_precision = None

        # From Database
        self._minimum_profit_rate = None
        self._maximum_order_cost = None

    def get_max_order_volume(self, price):
        return round(float(self.maximum_volume_in_btc / price), self.volume_step_size)

    @property
    def base_asset(self):
        with self.__lock:
            return self._base_asset

    @base_asset.setter
    def base_asset(self, value):
        with self.__lock:
            self._base_asset = value

    @property
    def quote_asset(self):
        with self.__lock:
            return self._quote_asset

    @quote_asset.setter
    def quote_asset(self, value):
        with self.__lock:
            self._quote_asset = value

    @property
    def price_precision(self):
        with self.__lock:
            return self._price_precision

    @price_precision.setter
    def price_precision(self, value):
        with self.__lock:
            self._price_precision = value

    @property
    def order_volume_step_size(self):
        with self.__lock:
            return self._order_volume_step_size

    @order_volume_step_size.setter
    def order_volume_step_size(self, value):
        with self.__lock:
            self._order_volume_step_size = value

    @property
    def minimum_order_volume(self):
        with self.__lock:
            return self._minimum_order_volume

    @minimum_order_volume.setter
    def minimum_order_volume(self, value):
        with self.__lock:
            self._minimum_order_volume = value

    @property
    def minimum_order_cost(self):
        with self.__lock:
            return self._minimum_order_cost

    @minimum_order_cost.setter
    def minimum_order_cost(self, value):
        with self.__lock:
            self._minimum_order_cost = value

    @property
    def order_volume_precision(self):
        with self.__lock:
            return self._order_volume_precision

    @order_volume_precision.setter
    def order_volume_precision(self, value):
        with self.__lock:
            self._order_volume_precision = value

    @property
    def order_limits_to_dict(self):
        with self.__lock:
            return {
                'order_volume_step_size': self.order_volume_step_size,
                'minimum_order_volume': self.minimum_order_volume,
                'minimum_order_cost': self.minimum_order_cost,
                'min_profit_rate': self.min_profit_rate,
                'order_volume_precision': self.order_volume_precision,
                'maximum_order_cost': self.maximum_order_cost,
            }

    @property
    def order_cost_limits_to_dict(self):
        with self.__lock:
            return {
                'minimum_order_cost': self.minimum_order_cost,
                'maximum_order_cost': self.maximum_order_cost,
            }

    @property
    def order_volume_limits_to_dict(self):
        with self.__lock:
            return {
                'minimum_order_volume': self.minimum_order_volume,
            }

    @property
    def order_rate_limits_to_dict(self):
        with self.__lock:
            return {
                'min_profit_rate': self.min_profit_rate,
            }

    @property
    def precisions_and_step_sizes_to_dict(self):
        with self.__lock:
            return {
                'price_precision': self.price_precision,
                'order_volume_precision': self.order_volume_precision,
                'order_volume_step_size': self.order_volume_step_size,
            }
