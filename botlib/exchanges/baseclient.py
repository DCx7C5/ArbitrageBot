import collections
import contextlib
import hashlib
import hmac
import json
import base64
import warnings
from threading import Lock
from urllib import parse
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

# SSL FIX
from botlib.sql_functions import get_max_order_size_for_exchange_sql, get_min_profit_for_exchange_sql

old_merge_environment_settings = Session.merge_environment_settings


class BaseClient:

    def __init__(self):
        self.lock = Lock()
        self.__session = Session()
        self.__headers = dict()
        self.__options = dict()
        self.balances = dict()
        self.min_profit = dict()
        self.max_order_size = dict()
        self.min_order_vol = dict()
        self.deposit_address = dict()
        self.withdrawal_fees = dict()
        self.maker_fees = dict()
        self.taker_fees = dict()
        self.last_call_mp = 0
        self.last_call_ms = 0
        self.last_call_moa = 0
        self.last_call_settings = 0
        self.name = None

    def api_call(self, endpoint, params, api):
        return self.__fetch_wrap(path=endpoint, params=params, api=api)

    def sign_data_for_prv_api(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            pass

    def update_balance(self):
        pass

    def __fetch_wrap(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = self.sign_data_for_prv_api(path, api, method, params, headers, body)
        return self.__fetch(request['url'], request['method'], request['headers'], request['body'])

    def __prepare_request_headers(self, headers=None):
        headers = headers or {}
        headers.update(self.__headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def __fetch(self, url, method='GET', headers=None, body=None):
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        self.__session.cookies.clear()
        with no_ssl_verification():
            response = self.__session.request(method=method, url=url, data=body,
                                              headers=request_headers,
                                              timeout=6)
        try:
            http_response = response.text
            json_data = json.loads(http_response)
            if json_data is not None:
                return json_data
            return http_response
        except InsecureRequestWarning:
            pass

    @staticmethod
    def _generate_path_from_params(params, endpoint):
        params_string = "?"
        for p in params:
            params_string += f'{p}={params[p]}' + "&"
        return f'{endpoint}{params_string[:-1]}'

    def __getitem__(self, item):
        return self.__getattribute__(item)
    
    @staticmethod
    def implode_params(string, params):
        if isinstance(params, dict):
            for key in params:
                if not isinstance(params[key], list):
                    string = string.replace('{' + key + '}', str(params[key]))
        return string

    @staticmethod
    def encode_uri_component(uri):
        return parse.quote(uri, safe="~()*!.'")

    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def url_encode(params=None):
        if params is None:
            params = {}
        if isinstance(params, dict) or isinstance(params, collections.OrderedDict):
            return parse.urlencode(params)
        return params

    @staticmethod
    def hmac(request, secret, algorithm=hashlib.sha256, digest='hex'):
        h = hmac.new(secret, request, algorithm)
        if digest == 'hex':
            return h.hexdigest()
        elif digest == 'base64':
            return base64.b64encode(h.digest())
        return h.digest()

    def update_min_profit(self):
        min_profits = get_min_profit_for_exchange_sql(self.name)
        for mp in min_profits:
            with self.lock:
                if mp not in self.min_profit:
                    self.min_profit.update({mp[1]: mp[0]})
                else:
                    self.min_profit[mp[1]] = mp[0]

    def update_max_order_size(self):
        max_orders = get_max_order_size_for_exchange_sql(self.name)
        for mo in max_orders:
            with self.lock:
                if mo not in self.max_order_size:
                    self.max_order_size.update({mo[1]: mo[0]})
                else:
                    self.max_order_size[mo[1]] = mo[0]

    def get_min_order_vol(self, refid):
        with self.lock:
            return self.min_order_vol.get(refid)

    def get_max_order_size(self, refid):
        with self.lock:
            return self.max_order_size.get(refid)

    def get_min_profit(self, refid):
        with self.lock:
            return self.min_profit.get(refid)


# noinspection PyBroadException
@contextlib.contextmanager
def no_ssl_verification():
    """
    Context wrapper function to catch and suppress SSL verification warnings
    with a simple 'with' clause. This class also changes the default value of
    requests.Session.verify_ssl and sets it to False
    """
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        opened_adapters.add(self.get_adapter(url))
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings
    Session.merge_environment_settings = merge_environment_settings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        Session.merge_environment_settings = old_merge_environment_settings
        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass
