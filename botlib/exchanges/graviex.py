import hmac
import threading
import time
from hashlib import sha256
from httpx import Request, request
from botlib import logger

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

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    @staticmethod
    def _generate_message_string(method, endpoint, params):
        params_str = ""
        for p in params:
            params_str += f"&{p}={params[p]}"
        return f'{method}|/api/v3{endpoint}|{params_str}'

    def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=sha256).hexdigest()

    def _api_call(self, method, endpoint, params, private=False):
        if private:
            params.update({'tonce': int(time.time() * 1000), 'access_key': self.api_key})
            msg_string = self._generate_message_string(method, endpoint, params)
            signature = self._generate_hash_signature(msg_string)
            params.update({'signature': signature})
        url = f'{BASEURL}{endpoint}'
        response = request(method=method, url=url, params=params)
        try:
            assert response.status_code == 200
            if response.json() is None:
                return response
            return response.json()
        except AssertionError as e:
            pass
        except TimeoutError as e:
            pass
        except RuntimeError as e:
            pass

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
        return self._api_call(POST, ORDERS, params=params, private=True)

    def _generate_deposit_address(self, coin):
        return self._api_call(endpoint=GEN_DEPOSIT, method=GET, params={'currency': coin}, private=True)

    def _list_account_history(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return self._api_call(endpoint=ACCOUNT, method=GET, params=params, private=True)

    def whoami(self):
        params = {}
        return self._api_call(endpoint=MEMBERS, method=GET, params=params, private=True)

    def get_deposit_address(self, coin) -> str:
        if self._generate_deposit_address(coin) == 'request_accepted':
            return self._api_call(endpoint=DEPOSIT_ADDR, method=GET, params={'currency': coin}, private=True)[1:-1]

    def get_withdrawal_fee(self, coin):
        pass

    def get_all_coin_tickers(self) -> dict:
        return self._list_tickers()

    def get_all_markets_by_name(self) -> list:
        return [m['name'] for m in self._list_markets()]

    def get_all_markets_by_id(self) -> list:
        return [m['id'] for m in self._list_markets()]

    def get_market_info_by_id(self, market_id) -> dict:
        return self._list_markets(market_id)

    def get_account_info(self):
        return self._list_account_history()

    def get_open_orders(self, market_id=None) -> list:
        if market_id is None:
            return self._list_orders()
        return self._list_orders(market=market_id)

    def get_open_order_ids(self) -> list:
        return [order['id'] for order in self.get_open_orders()]

    def cancel_order(self, order_id):
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self._api_call(POST, CANCEL, params=params, private=True)

    def create_buy_order(self, refi_id, volume, price=None):
        if price is None:
            return self._create_order(market=refi_id, side='buy', volume=volume)
        return self._create_order(market=refi_id, side='buy', volume=volume, price=price)

    def create_sell_order(self, market_id, volume, price=None):
        if price is None:
            return self._create_order(market=market_id, side='sell', volume=volume)
        return self._create_order(market=market_id, side='sell', volume=volume, price=price)

    def get_order_info(self, order_id):
        if not order_id:
            raise Exception('Order ID must be set')
        params = {'id': order_id}
        return self._api_call(GET, ORDER, params=params, private=True)

    def get_order_book(self, ref_id, limit=None):
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 100,
                  'asks_limit': limit if limit else 100}
        resp = self._api_call(endpoint=ORDER_BOOK, method=GET, params=params)
        return [(x['price'], x['volume']) for x in resp['bids']], [(x['price'], x['volume']) for x in resp['asks']]
