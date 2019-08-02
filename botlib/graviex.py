import asyncio
import time
import hmac
import hashlib

import requests

BASEURL = 'https://graviex.net/api/v3'

# API ENDPOINTS
MARKETS = '/markets'
TICKERS = '/tickers'
ACCOUNT = '/account/history'
ORDERS = '/orders'

# REQUEST METHODS
PUT = "PUT"
DELETE = "DELETE"
POST = "POST"
GET = "GET"

api_key = "gx4D8JHsxTdXQGd2kdOVVxxc1GOTPC8YAK1Bbwa3"
api_secret = "7KNZMzxUNDcfSPxOJWJZMlW98VeeXaw0EcJPSHQP"


class GraviexClient:

    def __init__(self, api_key, api_secret, calls_per_second=15, asyncbot=False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None
        if asyncbot is True:
            self._async_bot = True

    def _generate_request_string(self, params):
        params_string = ""
        for p in params:
            params_string += f'&{p}={params[p]}'
        return f'access_key={self.api_key}{params_string}&tonce={int(time.time() * 1000)}'

    def _generate_message_string(self, method, endpoint, params):
        req_string = self._generate_request_string(params=params)
        return f'{method}|/api/v3{endpoint}|{req_string}'

    def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()

    def _wait(self):
        if self._last_call is None:
            self._last_call = time.time()
        else:
            now = time.time()
            passed = now - self._last_call
            if passed < self.rate_limit:
                time.sleep(self.rate_limit - passed)
            self._last_call = time.time()

    async def _wait_async(self):
        if self._last_call is None:
            self._last_call = time.time()
        else:
            now = time.time()
            passed = now - self._last_call
            if passed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - passed)
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

        if method is POST:
            request = requests.post
        else:
            request = requests.get

        self._wait()

        response = request(url, params=params)

        assert response.status_code is 200

        return response.json()

    def _list_orders(self, market_id=None):
        params = {}
        endpoint = ORDERS
        if market_id:
            endpoint += "/" + market_id
        return self._api_call(endpoint=endpoint, method=GET, params=params)

    def _list_markets(self, market_id=None):
        params = {}
        endpoint = MARKETS
        if market_id:
            endpoint += "/" + market_id
        return self._api_call(endpoint=endpoint, method=GET, params=params)

    def _list_tickers(self, market_id=None):
        params = {}
        endpoint = TICKERS
        if market_id:
            endpoint += "/" + market_id
        return self._api_call(endpoint=endpoint, method=GET, params=params)

    def _list_account_history(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self._api_call(endpoint=ACCOUNT, method=GET, params=params)

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

    def get_open_orders(self, market_id=None):
        if market_id is None:
            return self._list_orders()
        return self._list_orders(market_id)
