import hashlib
import time
import urllib.parse as _url_encode
from collections import OrderedDict
from botlib.sql_functions import get_symbols_for_exchange_sql
from botlib.exchanges.baseclient import BaseClient


# API ENDPOINTS

DEPOSIT_ADDR = '/api/v3/deposit_address'
GEN_DEPOSIT = '/api/v3/gen_deposit_address'
BALANCE = '/api/v3/members/me'
ORDER = '/api/v3/order'
ORDER_BOOK = '/api/v3/order_book'
DEP_WIT_HISTORY = '/api/v3/account/history'
CREATE_ORDER = '/api/v3/orders'
STATUS_ORDER = '/api/v3/order'
DELETE_ORDER = '/api/v3/order/delete'

# REQUEST METHODS
POST = "POST"
GET = "GET"

BASE_URL = 'https://graviex.net'

PUBLIC = {'get': ['/order_book']}

PRIVATE = {
    'get': ['/account/history', '/orders', '/order'],
    'post': ['/orders', '/order']
}


class GraviexClient(BaseClient):

    def __init__(self, api_key, api_secret, calls_per_second=15):
        BaseClient.__init__(self)
        self.name = 'Graviex'
        self.__api_key = api_key
        self.__api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self.logger.debug(f'{self.name} initialized')

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = BASE_URL + path
        if api == 'private':
            nonce = round(time.time() * 1000)
            params.update({'tonce': nonce})
            params.update({'access_key': self.url_encode(self.__api_key)})
            o = OrderedDict(sorted(params.items()))
            params = {}
            for k in sorted(o):
                params.update({k: o[k]})
            query = _url_encode.urlencode(params)
            message = f'{method}|{path}|{query}'
            signature = self.hmac(message.encode(), self.__api_secret.encode(), hashlib.sha256)
            url += "?" + query + '&signature=' + signature
        else:
            url = self.generate_path_from_params(params, url)
        return {'url': url, 'method': method, 'body': body, 'headers': {}}

    def get_order_book(self, ref_id, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 50,
                  'asks_limit': limit if limit else 50}
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        while not resp:
            time.sleep(1.4)
            resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')

        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['bids']]:
            if p not in was_seen:
                was_seen.add(p)
                bids.append([round(float(p), 10), round(float(v), 10)])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += round(float(v), 10)
        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['asks']]:
            if p not in was_seen:
                was_seen.add(p)
                asks.append([round(float(p), 10), round(float(v), 10)])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += round(float(v), 10)
        return bids, asks

    def update_balance(self):
        response = self.api_call(endpoint=BALANCE, params={}, api='private')
        exch_symbols = [s for s in get_symbols_for_exchange_sql(self.name)] + [('btc', 'BTC')]
        for x in exch_symbols:
            for r in response['accounts_filtered']:
                if x[0] == r['currency']:
                    with self.lock:
                        self.balances.update(
                            {x[1]: r['balance']}
                        )

    def update_min_order_vol(self) -> None:
        # TODO FIND RIGHT API CALL FOR MIN ORDER VOLUME
        for i in self.balances.keys():
            self.min_order_vol.update({i: float(0.000001)})

    def create_order(self, refid, side, price, volume) -> int:
        params = {'market': refid, 'side': side, 'price': price, 'volume': volume}
        response = self.api_call(endpoint=CREATE_ORDER, params=params, api='private', method="POST")
        return response['id']

    def get_order_status(self, order_id) -> dict:
        return self.api_call(endpoint=STATUS_ORDER, params={'id': order_id}, api='private', method="GET")

    def cancel_order(self, order_id):
        return self.api_call(endpoint=DELETE_ORDER, params={'id': order_id}, api='private', method="POST")
