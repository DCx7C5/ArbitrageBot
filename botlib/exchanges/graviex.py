import hashlib
import time
import urllib.parse as _url_encode
from collections import OrderedDict

from botlib.exchanges.baseclient import BaseClient


# API ENDPOINTS
from botlib.sql_functions import get_symbols_for_exchange_sql

MARKETS = '/markets'
TICKERS = '/tickers'
ORDERS = '/orders'
DEPOSIT_ADDR = '/deposit_address'
GEN_DEPOSIT = '/gen_deposit_address'
MEMBERS = '/api/v3/members/me'
CANCEL = '/order/delete'
ORDER = '/order'
ORDER_BOOK = '/api/v3/order_book'
DEP_WIT_HISTORY = '/api/v3/account/history'
BALANCE = '/api/v3/fund_sources'

# REQUEST METHODS
POST = "POST"
GET = "GET"

BASE_URL = 'https://graviex.net'

PUBLIC = {'get': ['/api/v3/order_book', ]}

PRIVATE = {
    'get': ['/account/history', '/orders', '/order'],
    'post': ['/orders', '/order']
}


class GraviexClient(BaseClient):

    def __init__(self, api_key, api_secret, calls_per_second=15):
        BaseClient.__init__(self)
        self.name = 'Graviex'
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second

    def sign_data_for_prv_api(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = BASE_URL + path
        if api == 'private':
            nonce = round(time.time() * 1000)
            params.update({'tonce': nonce})
            params.update({'access_key': self.url_encode(self._api_key)})

            for i in PUBLIC.get('get') + PRIVATE.get('get'):
                if i in path:
                    method = "GET"
            for i in PRIVATE.get('post'):
                if i in path:
                    method = "POST"
            o = OrderedDict(sorted(params.items()))
            params = {}
            for k in sorted(o):
                params.update({k: o[k]})
            query = _url_encode.urlencode(params)

            message = f'{method}|{path}|{query}'
            print(message)
            signature = self.hmac(message.encode(), self._api_secret.encode(), hashlib.sha256)
            url += "?" + query + '&signature=' + signature
            print(url)
        else:
            url = self.generate_path_from_params(params, url)
        return {'url': url, 'method': method, 'body': body, 'headers': {}}

    def get_order_book(self, ref_id, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 25,
                  'asks_limit': limit if limit else 25}
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
        response = self.api_call(endpoint=BALANCE, params={'currency': "btc"}, api='private')
        exch_symbols = get_symbols_for_exchange_sql(self.name)
        print(response)
