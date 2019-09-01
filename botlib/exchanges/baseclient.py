import collections
import contextlib
import hashlib
import hmac
import json
import base64
import logging
import socket
import time
import warnings

import urllib3
from threading import Lock
from urllib import parse
from requests import Session
from requests.exceptions import ConnectionError
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings
from botlib.sql_functions import get_max_order_size_for_exchange_sql
from botlib.sql_functions import get_min_profit_for_exchange_sql
from botlib.bot_log import daemon_logger

logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

logger_api = daemon_logger.getChild('Cli')

# SSL FIX
disable_warnings()
old_merge_environment_settings = Session.merge_environment_settings


class BaseClient:

    def __init__(self):
        self.lock = Lock()
        self.name = None
        self.logger = logger_api
        self.logger.setLevel(logging.DEBUG)
        self.__session = Session()
        self.__headers = {}
        self.__options = {}
        self.balances = {}
        self.min_profit = {}
        self.max_order_size = {}
        self.min_order_vol = {}
        self.withdrawal_fees = {}
        self.maker_fees = {}
        self.taker_fees = {}

        self.last_call_mp = time.time()
        self.last_call_ms = time.time()
        self.last_call_moa = time.time()
        self.last_call_settings = time.time()
        self.__error_counter = 0
        self.logger.debug("ExchangeClients initialized")

    def api_call(self, endpoint, params, api):
        """Api call entry function for exchange api calls"""
        return self.fetch_wrap(path=endpoint, params=params, api=api)

    def fetch_wrap(self, path, api='public', method='GET', params=None, headers=None, body=None):
        """Wrapper function for base api request function"""
        if params is None:
            params = {}
        request = self.sign_data_for_prv_api(path, api, method, params, headers, body)
        return self.__fetch(request['url'], request['method'], request['headers'], request['body'])

    def __fetch(self, url, method='GET', headers=None, body=None):
        """Base api request function"""
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        self.__session.cookies.clear()
        try:
            with no_ssl_verification():
                response = self.__session.request(method=method, url=url, data=body,
                                                  headers=request_headers,
                                                  timeout=6)
            http_response = response.text
            json_data = json.loads(http_response)
            if json_data is not None:
                return json_data
            return http_response
        except Exception as error:
            self.error_handler(error)

    def __prepare_request_headers(self, headers=None):
        """"""
        headers = headers or {}
        headers.update(self.__headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    @staticmethod
    def generate_path_from_params(params, endpoint):
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

    def __update_min_profit(self) -> None:
        min_profits = get_min_profit_for_exchange_sql(self.name)
        for mp in min_profits:
            with self.lock:
                if mp not in self.min_profit:
                    self.min_profit.update({mp[1]: mp[0]})
                else:
                    self.min_profit[mp[1]] = mp[0]

    def __update_max_order_size(self) -> None:
        max_orders = get_max_order_size_for_exchange_sql(self.name)
        for mo in max_orders:
            with self.lock:
                if mo not in self.max_order_size:
                    self.max_order_size.update({mo[1]: mo[0]})
                else:
                    self.max_order_size[mo[1]] = mo[0]

    def get_min_order_vol(self, refid: str) -> float:
        with self.lock:
            mov = self.min_order_vol.get(refid)
        if (not mov) or time.time() > self.last_call_moa + 3600:
            self.update_min_order_vol()
            self.last_call_moa = time.time()
        with self.lock:
            return self.min_order_vol[refid]

    def get_max_order_size(self, refid: str) -> float:
        with self.lock:
            max_size = self.max_order_size.get(refid)
        if (not max_size) or time.time() > self.last_call_ms + 60:
            self.__update_max_order_size()
            self.last_call_mp = time.time()
        with self.lock:
            return self.max_order_size.get(refid)

    def get_min_profit(self, refid: str) -> float:
        with self.lock:
            min_profit = self.min_profit.get(refid)
        if (not min_profit) or time.time() > self.last_call_mp + 60:
            self.__update_min_profit()
            self.last_call_mp = time.time()
        with self.lock:
            return self.min_profit.get(refid)
    
    def get_available_balance(self, refid=None):
        with self.lock:
            balance = self.balances.get(refid)
        if not balance:
            self.update_balance()
        return self.balances.get(refid if refid else None)

    def update_balance(self):
        """
        Updates all coin balances for all symbols
            (Only here to be overwritten and to get referenced from here)
        """
        pass

    def update_min_order_vol(self):
        """Only here to be overwritten and to get referenced from here"""
        pass

    def sign_data_for_prv_api(self, path, api='public', method='GET', params=None, headers=None, body=None):
        """Only here to be overwritten and to get referenced from here"""
        pass

    def error_handler(self, error):
        """Manage session errors"""
        if isinstance(error, socket.timeout):
            self.logger.critical('socket.timeout')
        if isinstance(error, ConnectionError):
            self.logger.error('ConnectionError')
        if isinstance(error, urllib3.exceptions.ReadTimeoutError):
            self.logger.error('ReadTimeoutError | Caused by owm session timeout values')
        # if isinstance(error, json.decoder.JSONDecodeError):
        #     self.logger.error('JSONDecodeError | Happens if response is NoneType')
        if isinstance(error, InsecureRequestWarning):
            self.logger.warning('InsecureRequestWarning | Caused by SSL "hack"')
        if isinstance(error, TypeError):
            self.logger.warning('TypeError | Still unknown')

        self.__error_counter += 1
        if self.__error_counter > 3:
            self.__session.close()
            self.__session = Session()


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
