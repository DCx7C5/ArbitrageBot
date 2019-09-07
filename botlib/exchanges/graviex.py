import hashlib
import time
import urllib.parse as _url_encode
from collections import OrderedDict

from botlib.bot_utils import generate_path_from_params, hmac_val, url_encode
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
MARKETS = '/api/v3/markets'
SETTINGS = '/api/v3/settings/get'

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
    """Graviex Exchange API Client"""
    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        super().__init__()
        self.name = 'Graviex'
        self.rate_limit = 1.0 / 15

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = BASE_URL + path
        if api == 'private':
            nonce = round(time.time() * 1000)
            params.update({'tonce': nonce})
            params.update({'access_key': url_encode(self.api_key)})
            o = OrderedDict(sorted(params.items()))
            params = {}
            for k in sorted(o):
                params.update({k: o[k]})
            query = _url_encode.urlencode(params)
            message = f'{method}|{path}|{query}'
            signature = hmac_val(message.encode(), self.api_secret.encode(), hashlib.sha256)
            url += "?" + query + '&signature=' + signature
        else:
            url = generate_path_from_params(params, url)
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
            time.sleep(.15)
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

    def update_min_order_vol(self) -> None:
        # TODO FIND RIGHT API CALL FOR MIN ORDER VOLUME
        for i in self.balances.keys():
            self.min_order_vol.update({i: float(0.000001)})

    def create_order(self, refid, side, price, volume) -> dict:
        params = {'market': refid, 'side': side, 'price': price, 'volume': volume}
        response = self.api_call(endpoint=CREATE_ORDER, params=params, api='private', method="POST")
        return {
            'order_id': response['id'],
            'refid': refid,
            'status': response['state'],
            'side': side,
            'price': response['price'],
            'volume': response['volume'],
            'executed_volume': response['executed_volume']
        }

    def get_order_status(self, order_id):
        response = self.api_call(endpoint=STATUS_ORDER, params={'id': order_id}, api='private', method="GET")
        return self.name, response['state'], response['executed_volume']

    def cancel_order(self, order_id):
        response = self.api_call(endpoint=DELETE_ORDER, params={'id': order_id}, api='private', method="POST")
        if response:
            return "done"
        return None

    def update_all_markets(self):
        resp = self.api_call(endpoint=MARKETS, params={}, api='public')
        for m in self.markets.keys():
            for market in resp:
                self.markets[m].update({market["id"]: {}})

    def update_all_balances(self):
        response = self.api_call(endpoint=BALANCE, params={'limit': 555}, api='private')
        for symbol in response["accounts_filtered"]:
            self.balances.update({symbol['currency']: {'available': symbol['balance'], 'locked': symbol['locked']}})
