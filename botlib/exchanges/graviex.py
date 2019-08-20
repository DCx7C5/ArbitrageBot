import hmac
import json
import time
from hashlib import sha256
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASE_URL = 'https://graviex.net/api/v3'

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
FUNDS = '/fund_sources'

# REQUEST METHODS
POST = "POST"
GET = "GET"


class GraviexClient:

    def __init__(self, api_key, api_secret, calls_per_second=15):
        self.__api_key = api_key
        self.__api_secret = api_secret
        self.__rate_limit = 1.0 / calls_per_second
        self.__last_call = None

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    @staticmethod
    def __generate_path(params, endpoint):
        params_string = "?"
        for p in params:
            params_string += f'{p}={params[p]}' + "&"
        return f'{endpoint}{params_string[:-1]}'

    def __generate_hash_signature(self, method, path):
        return hmac.new(key=self.__api_secret.encode(),
                        msg=f'{method}|/api/v3{path}'.encode(),
                        digestmod=sha256).hexdigest()

    def __api_call(self, method, endpoint, params):
        if not params:
            params = {}
        path = self.__generate_path(params, endpoint)
        url = f'{BASE_URL}{path}'
        params.update({'tonce': int(time.time() * 1000), 'access_key': self.__api_key})
        signature = self.__generate_hash_signature(method, path)
        params.update({'signature': signature})
        request = Request(url)
        request.method = method
        try:
            response = urlopen(request)
        except HTTPError as e:
            response = e
        return json.loads(bytes.decode(response.read()))

    def __list_orders(self, **kwargs):
        params = {'market': 'all'}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self.__api_call(endpoint=ORDERS, method=GET, params=params)

    def __list_markets(self, market_id=None):
        params = {}
        endpoint = MARKETS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return self.__api_call(endpoint=endpoint, method=GET, params=params)

    def __list_tickers(self, market_id=None):
        params = {}
        endpoint = TICKERS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return self.__api_call(endpoint=endpoint, method=GET, params=params)

    def __create_order(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self.__api_call(POST, ORDERS, params=params)

    def __generate_deposit_address(self, coin):
        return self.__api_call(endpoint=GEN_DEPOSIT, method=GET, params={'currency': coin})

    def __list_account_history(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self.__api_call(endpoint=ACCOUNT, method=GET, params=params)

    def whoami(self):
        params = {}
        return self.__api_call(endpoint=MEMBERS, method=GET, params=params)

    def get_deposit_address(self, coin) -> str:
        if self.__generate_deposit_address(coin) == 'request_accepted':
            return self.__api_call(endpoint=DEPOSIT_ADDR, method=GET, params={'currency': coin})[1:-1]

    def get_all_coin_tickers(self) -> dict:
        return self.__list_tickers()

    def get_all_markets_by_name(self) -> list:
        return [m['name'] for m in self.__list_markets()]

    def get_all_markets_by_id(self) -> list:
        return [m['id'] for m in self.__list_markets()]

    def get_market_info_by_id(self, market_id) -> dict:
        return self.__list_markets(market_id)

    def get_account_info(self):
        return self.__list_account_history()

    def get_open_orders(self, market_id=None) -> list:
        if market_id is None:
            return self.__list_orders()
        return self.__list_orders(market=market_id)

    def get_open_order_ids(self) -> list:
        return [order['id'] for order in self.get_open_orders()]

    def cancel_order(self, order_id):
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self.__api_call(POST, CANCEL, params=params)

    def create_buy_order(self, refi_id, volume, price=None):
        if price is None:
            return self.__create_order(market=refi_id, side='buy', volume=volume)
        return self.__create_order(market=refi_id, side='buy', volume=volume, price=price)

    def create_sell_order(self, market_id, volume, price=None):
        if price is None:
            return self.__create_order(market=market_id, side='sell', volume=volume)
        return self.__create_order(market=market_id, side='sell', volume=volume, price=price)

    def get_order_info(self, order_id):
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self.__api_call(GET, ORDER, params=params)

    def get_order_book(self, ref_id, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 100,
                  'asks_limit': limit if limit else 100}
        resp = self.__api_call(endpoint=ORDER_BOOK, method=GET, params=params)

        # Volume addition of redundant positions
        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['bids']]:
            if p not in was_seen:
                was_seen.add(p)
                bids.append([p, v])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += v
        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['asks']]:
            if p not in was_seen:
                was_seen.add(p)
                asks.append([p, v])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += v
        return bids, asks

    def get_balance(self, ref_id):
        currency = ref_id.lower()
        currency = currency.replace('btc', '') if ref_id != "btc" else None
        params = {"currency": currency}
        return self.__api_call(endpoint=FUNDS, method=GET, params=params)
