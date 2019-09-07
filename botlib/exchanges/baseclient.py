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

from botlib.bot_utils import number_to_string
from botlib.sql_functions import get_max_order_size_for_exchange_sql
from botlib.sql_functions import get_min_profit_for_exchange_sql
from botlib.bot_log import daemon_logger

from botlib.decimal_to_precision import DECIMAL_PLACES, TRUNCATE, ROUND
from botlib.decimal_to_precision import decimal_to_precision


logging.getLogger("requests").setLevel(logging.INFO)
logging.getLogger("urllib3").setLevel(logging.INFO)

logger_api = daemon_logger.getChild('Cli')

# SSL FIX
disable_warnings()
old_merge_environment_settings = Session.merge_environment_settings


class BaseClient:
    """
    Exchange Client Base Class
    """
    def __init__(self):
        self.name = None
        self.lock = Lock()

        self.logger = logger_api
        self.logger.setLevel(logging.DEBUG)
        self.session = Session()
        self.headers = {}

        # Dictionary contains all coin balances
        self.balances = {}
        self.balances_keys = 'market'

        # Dictionary with refid keys (contains all market settings)
        self.markets = {}

        # Dictionary with timestamps for timer based management of function calls
        self.last_calls = {
            'private_api': time.time(),
            'min_profit_rate': time.time(),
            'maximum_order_size': time.time(),
            'minimum_order_volume': time.time(),
        }

        self.precisionMode = DECIMAL_PLACES

        self.min_profit = {}
        self.max_order_size = {}
        self.min_order_vol = {}
        self.withdrawal_fees = {}
        self.maker_fees = {}
        self.taker_fees = {}

        self.error_counter = 0
        self.decimal_to_precision = decimal_to_precision
        self.num_to_str = number_to_string

        self.init_exchange_settings()

    # Response Management

    def api_call(self, endpoint, params, api="public", method="GET"):
        """Api call entry function for exchange api calls"""
        return self.__fetch_wrap(path=endpoint, params=params, api=api, method=method)

    def __fetch_wrap(self, path, api, method, params=None, headers=None, body=None):
        """Wrapper function for base api request function"""
        if params is None:
            params = {}
        request = self.sign_request(path, api, method, params, headers, body)
        return self.__fetch(request['url'], request['method'], request['headers'], request['body'])

    def __fetch(self, url, method='GET', headers=None, body=None):
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
        """"""
        headers = headers or {}
        headers.update(self.headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def update_min_profit(self) -> None:
        min_profits = get_min_profit_for_exchange_sql(self.name)
        for mp in min_profits:
            with self.lock:
                if mp not in self.min_profit:
                    self.min_profit.update({mp[1]: mp[0]})
                else:
                    self.min_profit[mp[1]] = mp[0]

    def update_max_order_size(self) -> None:
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
            return float(self.min_order_vol[refid])

    def get_max_order_size(self, refid: str) -> float:
        with self.lock:
            max_size = self.max_order_size.get(refid)
        if (not max_size) or time.time() > self.last_call_ms + 60:
            self.update_max_order_size()
            self.last_call_mp = time.time()
        with self.lock:
            return self.max_order_size.get(refid)

    def get_min_profit(self, refid: str) -> float:
        with self.lock:
            min_profit = self.min_profit.get(refid)
        if (not min_profit) or time.time() > self.last_call_mp + 60:
            self.update_min_profit()
            self.last_call_mp = time.time()
        with self.lock:
            return self.min_profit.get(refid)

    def get_available_balance(self, refid=None):
        balance = self.balances.get(refid)
        if not balance:
            self.update_all_balances()
        with self.lock:
            return self.balances.get(refid)

    def init_exchange_settings(self):
        # Create keys in self.markets
        self.create_markets_dictionary()

        # Create all markets for self.markets
        self.update_all_markets()

        # Get all coin balances
        self.update_all_balances()

    def create_markets_dictionary(self):
        self.markets.update(
            {
                'withdrawal_fee': {},             # Cost for making withdrawals on market
                'withdrawal_allowed': {},         # Withdrawals allowed
                'min_withdrawal_volume': {},      # Minimum allowed withdrawal amount
                'max_withdrawal_volume': {},      # Maximum allowed withdrawal amount
                'withdrawal_precision': {},       #
                'min_deposit_volume': {},         # Minimum allowed volume deposits
                'deposits_allowed': {},
                'deposit_address': {},            # Address of the bot market
                'symbol': {},                     # Market
                'max_order_vol_btc': {},          # Max order volume in BTC from database
                'min_order_price': {},            # Min order price of coin
                'min_order_volume': {},           # Min order volume of coin
                'min_ticker_size': {},            # The minimum price movement of the market ticker
                'maker_fees': {},                 # Fees for buy orders
                'taker_fees': {},                 # Fees for sell orders
                'market_status': {}              # Market status on exchange (on/off) True/False
            }
        )

    def calculate_fee(self, symbol, side, amount, price, order_type="limit", taker_or_maker='taker', params=None):
        if params is None:
            params = {}
        market = self.markets[symbol]
        rate = market[taker_or_maker]
        cost = float(self.cost_to_precision(symbol, amount * price))
        return {
            'rate': rate,
            'type': taker_or_maker,
            'currency': market['quote'],
            'cost': float(self.fee_to_precision(symbol, rate * cost)),
        }

    def cost_to_precision(self, symbol, cost):
        return self.decimal_to_precision(cost, ROUND, self.markets[symbol]['precision']['price'], self.precisionMode)

    def price_to_precision(self, symbol, price):
        return self.decimal_to_precision(price, ROUND, self.markets[symbol]['precision']['price'], self.precisionMode)

    def amount_to_precision(self, symbol, amount):
        return self.decimal_to_precision(amount, TRUNCATE, self.markets[symbol]['precision']['amount'], self.precisionMode)

    def fee_to_precision(self, symbol, fee):
        return self.decimal_to_precision(fee, ROUND, self.markets[symbol]['precision']['price'], self.precisionMode)

    def currency_to_precision(self, currency, fee):
        return self.decimal_to_precision(fee, ROUND, self.markets[currency]['precision'], self.precisionMode)

    def create_order(self, ref_id, side, price, volume):
        return dict()

    def update_all_markets(self):
        pass

    def get_order_status(self, order_id):
        pass

    def update_all_balances(self):
        pass

    def cancel_order(self, order_id):
        pass

    def update_min_order_vol(self):
        pass

    def update_deposit_address(self, refid):
        pass

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
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

    def __getitem__(self, item):
        return self.__getattribute__(item)

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
