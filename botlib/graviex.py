import json
import threading
import time
import hmac
from hashlib import sha256
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASEURL = 'https://graviex.net/api/v3'

# API ENDPOINTS
MARKETS = '/markets'
TICKERS = '/tickers'
ACCOUNT = '/account/history'
ORDERS = '/orders'
DEPOSIT_ADDR = '/deposit_address'
GEN_DEPOSIT = '/gen_deposit_address'
MEMBERS = '/members/me'
CANCEL = '/order/delete'
ORDER = '/order'
ORDER_BOOK = '/order_book'

# REQUEST METHODS
POST = "POST"
GET = "GET"


class GraviexClient:

    def __init__(self, api_key, api_secret, calls_per_second=15):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None
        self._wait_lock = threading.RLock()

    def _generate_request_string(self, params):
        params_string = ""
        for p in params:
            params_string += f'&{p}={params[p]}'
        return f'access_key={self.api_key}{params_string}&tonce={int(time.time() * 1000)}'

    def _generate_message_string(self, method, endpoint, params):
        return f'{method}|/api/v3{endpoint}|{self._generate_request_string(params=params)}'

    def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=sha256).hexdigest()

    def _wait(self):
        with self._wait_lock:
            if self._last_call is None:
                self._last_call = time.time()
            else:
                now = time.time()
                passed = now - self._last_call
                if passed < self.rate_limit:
                    time.sleep(self.rate_limit - passed)
                self._last_call = time.time()

    def _api_call(self, method: str,
                  endpoint: str,
                  params: dict = None):
        """
        BASE FUNCTION FOR MAKING API CALLS TO GRAVIEX
        """
        if not params:
            params = {}
        else:
            params = params
        
        req_string = self._generate_request_string(params=params)

        msg_string = self._generate_message_string(method=method, endpoint=endpoint, params=params)

        signature = self._generate_hash_signature(msg_string)

        url = f'{BASEURL}{endpoint}?{req_string}&signature={signature}'

        params.update({'signature': signature})

        self._wait()

        request = Request(url)

        request.method = method

        self._wait()

        try:
            response = urlopen(request)
        except HTTPError as e:
            response = e
        return json.loads(bytes.decode(response.read()))

    def _list_orders(self, **kwargs):
        params = {'market': 'all'}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self._api_call(endpoint=ORDERS, method=GET, params=params)

    def _list_markets(self, market_id=None):
        params = {}
        endpoint = MARKETS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return self._api_call(endpoint=endpoint, method=GET, params=params)

    def _list_tickers(self, market_id=None):
        params = {}
        endpoint = TICKERS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return self._api_call(endpoint=endpoint, method=GET, params=params)

    def _create_order(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self._api_call(POST, ORDERS, params=params)

    def _generate_deposit_address(self, coin):
        return self._api_call(endpoint=GEN_DEPOSIT, method=GET, params={'currency': coin})

    def _list_account_history(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self._api_call(endpoint=ACCOUNT, method=GET, params=params)

    def whoami(self):
        return self._api_call(endpoint=MEMBERS, method=GET)

    def get_deposit_address(self, coin) -> str:
        """
        Returns deposit address for coin as string
        """
        if self._generate_deposit_address(coin) == 'request_accepted':
            return self._api_call(endpoint=DEPOSIT_ADDR, method=GET, params={'currency': coin})[1:-1]

    def get_withdrawal_fee(self, coin):
        pass

    def get_all_coin_tickers(self) -> dict:
        """
        Returns dictionary with all coin tickers
        """
        return self._list_tickers()

    def get_ticker(self, coin) -> dict:
        """
        Returns a coin ticker
        """
        return self._list_tickers(coin)

    def get_all_markets_by_name(self) -> list:
        """
        Returns a list of all available market pairs
        """
        return [m['name'] for m in self._list_markets()]

    def get_all_markets_by_id(self) -> list:
        """
        Returns a list of all available market pair ids
        """
        return [m['id'] for m in self._list_markets()]

    def get_market_info_by_id(self, market_id) -> dict:
        """
        Returns a dictionary with with market infos for specific pair
        """
        return self._list_markets(market_id)

    def get_account_info(self):
        return self._list_account_history()

    def get_open_orders(self, market_id=None) -> list:
        """
        Returns list(dict(),) with open orders
        """
        if market_id is None:
            return self._list_orders()
        return self._list_orders(market=market_id)

    def get_open_order_ids(self) -> list:
        """
        Returns list with open order IDs
        """
        return [order['id'] for order in self.get_open_orders()]

    def cancel_order(self, order_id):
        """
        Cancels Order by order_id and returns True
        """
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self._api_call(POST, CANCEL, params=params)

    def create_buy_order(self, market_id, amount, price=None):
        """
        Creates buy order for market_id: ex: 'rvnbtc'
        """
        if price is None:
            return self._create_order(market=market_id, side='buy', volume=amount)
        return self._create_order(market=market_id, side='buy', volume=amount, price=price)

    def create_sell_order(self, market_id, amount, price=None):
        """
        Creates sell order for market_id: ex: 'rvnbtc'
        """
        if price is None:
            return self._create_order(market=market_id, side='sell', volume=amount)
        return self._create_order(market=market_id, side='sell', volume=amount, price=price)

    def get_order_info(self, order_id):
        """
        Gives information about order_id
        """
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self._api_call(GET, ORDER, params=params)


