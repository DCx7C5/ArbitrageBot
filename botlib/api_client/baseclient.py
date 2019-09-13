import contextlib
import json
import logging
import socket
import time
import warnings

import urllib3
from threading import Lock, Thread
from requests import Session
from requests.exceptions import ConnectionError
from urllib3.exceptions import InsecureRequestWarning
from urllib3 import disable_warnings

from botlib.bot_log import api_logger
from botlib.api_client.client_utils import MarketManager
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
    _name = None
    _rate_limit = None
    _taker_fees = None
    _maker_fees = None
    _withdrawal_fees = None

    def __init__(self):
        self.name = self._name
        self.rate_limit = self._rate_limit if self._rate_limit is not None else 7
        self.taker_fees = self._taker_fees if self._taker_fees is not None else 0.2
        self.maker_fees = self._maker_fees if self._maker_fees is not None else 0.2
        self.withdrawal_fees = self._withdrawal_fees if self._withdrawal_fees is not None else 0.1

        self.__lock = Lock()
        self.logger = api_logger
        self.logger.setLevel(logging.DEBUG)
        self.session = Session()
        self.headers = {}

        # Dictionary contains all coin balances
        self.balances = {}

        # Dictionary with timestamps for timer based management of function calls
        self.last_calls = {
            'private_api': 0,
            'min_profit_rate': 0,
            'maximum_order_size': 0,
            'minimum_order_volume': 0,
            'fetch_all_markets': 0,
            'fetch_all_balances': 0,
            'update_market_settings': 0
        }

        self.markets = None

    def update_market_settings(self) -> None:
        api_data = self.parse_all_market_information()
        sql_data = get_market_data_sql(self._name)
        with self.__lock:
            self.markets = MarketManager(api_data, sql_data)

    def get_balance(self, refid: str) -> float:
        """Returns a coin/asset balance"""
        symbol = get_one_symbol_from_exchange_sql(self._name, refid)
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
        return self.parse_canceled_order(status_response)

    def get_crypto_deposit_address(self, refid):
        deposit_response = self.fetch_deposit_address(refid)
        return self.parse_deposit_address(deposit_response)

    def create_crypto_withdrawal(self, refid, amount, address):
        withdrawal_response = self.create_withdrawal(refid, amount, address)
        return self.parse_withdrawal(withdrawal_response)

    def get_order_rate_limits(self, refid) -> dict:
        with self.__lock:
            return self.markets[refid].get_order_rate_limits()

    def get_order_cost_limits(self, refid) -> dict:
        with self.__lock:
            return self.markets[refid].order_cost_limits_to_dict()

    def get_order_volume_limits(self, refid) -> dict:
        with self.__lock:
            return self.markets[refid].order_volume_limits_to_dict()

    def get_transaction_limits(self, refid) -> dict:
        with self.__lock:
            return self.markets[refid].order_limits_to_dict()

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
        """
        Parse exchange specific create_order response to bot and db format
        :rtype: dict
        :returns:
            e.g.:
                    {
                        'refid': "dogebtc",
                        'order_id': 3244844,
                        'status': "done" or "",
                        'side': "buy" or "sell"
                        'price': 0.00003234,
                        'volume': 102.00303.
                        'executed_volume': 77.997,
                        'created': datetime,
                        'modified': datetime
                    }
        """
        pass

    def fetch_order_status(self, order_id, refid=None):
        pass

    def parse_order_status(self, raw_response) -> dict:
        """
        Parse exchange specific create_order response to bot and db format
        :rtype: dict
        :returns:
            e.g.:
                    {
                        'refid': "dogebtc",
                        'order_id': 3244844,
                        'status': "done" or "",
                        'side': "buy" or "sell"
                        'price': 0.00003234,
                        'volume': 102.00303.
                        'executed_volume': 77.997,
                        'created': datetime,
                        'modified': datetime
                    }
        """

        pass

    def cancel_order(self, order_id, refid=None):
        pass

    def parse_canceled_order(self, raw_response) -> bool:
        pass

    def parse_all_market_information(self) -> list:
        pass

    def fetch_all_balances(self) -> list:
        pass

    def fetch_deposit_address(self, refid):
        pass

    def parse_deposit_address(self, raw_response) -> str:
        pass

    def create_withdrawal(self, refid, amount, address):
        pass

    def parse_withdrawal(self, withdrawal_response) -> dict:
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


def save_to_db(func):
    def wrapper(self, *args, **kwargs):
        resp = func(self, *args, **kwargs)
        return resp
    return wrapper


def no_errors(func):
    # noinspection PyBroadException
    def wrapper(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except:
            pass
    return wrapper


def private(func):
    def wrapper(self, *args, **kwargs):
        rate_limit = self.rate_limit
        last_call = self.last_calls['private_api']
        private_api_elapsed = time.time() - last_call
        if private_api_elapsed < rate_limit:
            delay = rate_limit - private_api_elapsed
            time.sleep(delay / 1000.0)
        value = func(self, *args, **kwargs)
        self.last_calls['private_api'] = time.time()
        return value
    return wrapper


def update_balances(func):
    def wrapper(*args, **kwargs):
        value = func(*args, **kwargs)
        Thread(target=func, args=args, kwargs=kwargs).start()
        return value
    return wrapper
