import contextlib
import json
import logging
import socket
import time
import warnings

import urllib3
from threading import Lock
from requests import Session
from requests.exceptions import ConnectionError
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from botlib.bot_log import api_logger
from botlib.api_client.market_manager import MarketManager
from botlib.sql_functions import get_one_symbol_from_exchange_sql, get_market_data_sql

logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

# SSL FIX
disable_warnings()
old_merge_environment_settings = Session.merge_environment_settings


class BaseClient:
    """
    Exchange Client Base Class

    """
    name = None
    rate_limit = None
    taker_fees = None
    maker_fees = None
    transaction_fee_type = 'percentage'
    trading_fee_type = 'percentage'
    __api_key, __api_secret = None, None

    def __init__(self):
        self.name = self.name
        self.rate_limit = self.rate_limit if self.rate_limit is not None else 7
        self.taker_fees = self.taker_fees if self.taker_fees is not None else 0.2
        self.maker_fees = self.maker_fees if self.maker_fees is not None else 0.2

        self.__lock = Lock()
        self.logger = api_logger
        self.logger.setLevel(logging.DEBUG)
        self.session = Session()
        self.headers = {}

        # Dictionary contains all coin balances
        self.balances = {}

        # Dictionary with timestamps for timer based management of function calls
        self.last_calls = {
            'private_api': float(0),
            'update_balances': float(0),
            'update_market_settings': float(0)
        }

        self.markets = None

    def update_market_settings(self) -> None:
        api_data = self.parse_all_market_information()
        sql_data = get_market_data_sql(self.name)
        with self.__lock:
            self.markets = MarketManager(api_data, sql_data)
        self.last_calls['update_market_settings'] = time.time()

    def get_balance(self, refid: str) -> float:
        """Returns a coin/asset balance"""
        if not refid == 'BTC':
            symbol = get_one_symbol_from_exchange_sql(self.name, refid)
        else:
            symbol = refid
        with self.__lock:
            bal = self.balances.get(symbol)
            if not bal:
                self.update_balances()
                return self.balances.get(symbol)
        return bal

    def update_balances(self):
        """Updates internal exchange specific balance dictionary"""
        for bal in self.fetch_all_balances():
            with self.__lock:
                if bal['symbol'] not in self.balances.keys():
                    self.balances[bal['symbol']] = float(bal['available'])
        self.last_calls['update_balances'] = time.time()

    def calculate_trading_fees(self):
        pass

    def create_limit_order(self, refid, price, volume, side):
        """Create standard limit order"""
        precision = self.markets[refid].order_volume_precision
        step_size = self.markets[refid].order_volume_step_size
        volume = round(float((volume // step_size) * step_size), precision)
        create_ord_response = self.create_order(refid, side, price, volume)
        return self.parse_created_order(create_ord_response)

    def cancel_limit_order(self, order_id, refid=None):
        cancel_response = self.cancel_order(order_id, refid)
        return self.parse_canceled_order(cancel_response)

    def get_order_status(self, order_id, refid=None):
        status_response = self.fetch_order_status(order_id, refid)
        return self.parse_order_status(status_response)

    def get_crypto_deposit_address(self, refid):
        deposit_response = self.fetch_deposit_address(refid)
        return self.parse_deposit_address(deposit_response)

    def create_crypto_withdrawal(self, refid, amount, address):
        withdrawal_response = self.create_withdrawal(refid, amount, address)
        return self.parse_withdrawal(withdrawal_response)

    def get_minimum_profit_rate(self, refid) -> float:
        """Calls rate limit dictionary from market manager class"""
        return self.markets[refid].minimum_profit_rate

    def get_limits(self, refid) -> dict:
        """Calls limit dictionary from market manager class"""
        return self.markets[refid].market_limits_to_dict()

    # Response management functions

    def _api_call(self, endpoint, params, api="public", method="GET"):
        """Api call entry function for exchange api calls"""
        return self._fetch_wrap(path=endpoint, params=params, api=api, method=method)

    def _fetch_wrap(self, path, api, method, params=None, headers=None, body=None):
        """Wrapper function for base api request function"""
        if params is None:
            params = {}
        request = self.sign_request(path, api, method, params, headers, body)
        return self._fetch(request['url'], request['method'], request['headers'], request['body'])

    def _fetch(self, url, method="GET", headers=None, body=None):
        """Base api request function"""
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        self.session.cookies.clear()
        try:
            with no_ssl_verification():
                response = self.session.request(
                    method=method, url=url, data=body,
                    headers=request_headers,
                    timeout=6
                )
            http_response = response.text
            json_data = json.loads(http_response)
            if json_data is not None:
                return json_data
            return http_response
        except Exception as error:
            self.error_handler(error)

    def __prepare_request_headers(self, headers=None):
        headers = headers or {}
        headers.update(self.headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

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

    def __getitem__(self, item):
        return self.__getattribute__(item)

    # Referencing subclass functions for scope and docstrings

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        """Used for signing requests to private api endpoints"""
        pass

    def create_order(self, refid: str, side: str, price: float, volume: float):
        """Creates order that still needs to be parsed to bot format"""
        pass

    def parse_created_order(self, raw_response):
        """Parse exchange specific create_order response to bot and db format"""
        pass

    def fetch_order_status(self, order_id, refid=None):
        pass

    def parse_order_status(self, raw_response) -> dict:
        """Parse exchange specific create_order response to bot and db format"""
        pass

    def cancel_order(self, order_id, refid=None):
        pass

    def parse_canceled_order(self, raw_response) -> bool:
        """
        Parse exchange specific cancel_order response to bot and db format
        """
        pass

    def parse_all_market_information(self) -> list:
        """
        Parse exchange specific market/asset information
        """
        pass

    def fetch_all_balances(self) -> list:
        pass

    def fetch_deposit_address(self, refid):
        pass

    def parse_deposit_address(self, raw_response) -> str:
        """Parse deposit address from raw response"""
        pass

    def create_withdrawal(self, refid, amount, address):
        """Creates withdrawal api request"""
        pass

    def parse_withdrawal(self, withdrawal_response) -> dict:
        """Parse exchange specific withdrawal response"""
        pass

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


def force_result(func):
    """Repeats function 3 times, then gives up"""
    def _wrapper(self, *args, **kwargs):
        resp = None
        counter = 0
        while resp is None:
            resp = func(self, *args, **kwargs)
            if not resp:
                counter += 1
                api_logger.warning(f"Failed to force function result: {counter} times."
                                   f"Giving up now. {func.__name__} on exchange {self.name}")
                if counter == 4:
                    api_logger.critical(f"Forced function result 3 times."
                                        f" Giving up now. {func.__name__} on exchange {self.name}")
                    break
                time.sleep(1 * (counter + 1))
                continue
            else:
                return resp
        return False
    return _wrapper


def no_errors(func):
    """Suppresses all possible response errors"""
    # noinspection PyBroadException
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:

            pass
    return wrapper


def private(func):
    """Wraps exchange specific private api routines around a private function call"""
    def _wrapper(self, *args, **kwargs):
        rate_limit = self.rate_limit
        last_call = self.last_calls['private_api']
        private_api_elapsed = time.time() - last_call
        if private_api_elapsed < rate_limit:
            delay = rate_limit - private_api_elapsed
            time.sleep(delay / 1000.0)
        value = func(self, *args, **kwargs)
        self.last_calls['private_api'] = time.time()
        return value
    return _wrapper


def log_timestamps(func):
    """Logs timestamps for important exchange calls"""
    def _wrapper(self, *args, **kwargs):
        last_call_ts = self.last_calls.get(func.__name__)[0]
        call_after_secs = self.last_calls.get(func.__name__)[1]
        if last_call_ts and (time.time() > (last_call_ts + call_after_secs)):
            pass
        last_calls_key = func.__name__
