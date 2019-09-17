import hashlib
import time
import urllib.parse as _url_encode
from collections import OrderedDict

from botlib.api_client.client_utils import generate_path_from_params, hmac_val, url_encode, to_database_time
from botlib.api_client.baseclient import BaseClient, private, no_errors, force_result

# API ENDPOINTS
from botlib.sql_functions import get_key_and_secret_sql

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
TICKERS = '/api/v3/tickers'
INFO = '/api/v3/currency/info'


# REQUEST METHODS
POST = "POST"
GET = "GET"

BASE_URL = 'https://graviex.net'

ORDER_STATES = {
    'new': ['wait'],
    'all_filled': ['done'],
    'partially_filled': ['wait'],
    'canceled': ['cancel'],
}


class GraviexClient(BaseClient):
    """Graviex Exchange API Client"""

    name = "Graviex"
    rate_limit = 1.0 / 15
    maker_fees = 0.2
    taker_fees = 0.2
    transaction_fee_type = 'static'  # the fee amount is -0.002 Coin, except...
    __api_key, __api_secret = get_key_and_secret_sql(name)

    @force_result
    def parse_all_market_information(self):
        resp = self._api_call(endpoint=TICKERS, params={}, api='public')
        return [
            {
                'refid': market,
                'base_asset': resp[market]['base_unit'],
                'quote_asset': resp[market]['quote_unit'],
                'minimum_order_volume': resp[market]['base_min'],
                'price_precision': resp[market]['quote_fixed'],
                'order_volume_precision': resp[market]['base_fixed'],
                'order_volume_step_size': resp[market]['base_min'],
                'minimum_order_cost': None,

            } for market in resp
        ]

    @private
    def fetch_all_balances(self):
        resp = self._api_call(endpoint=BALANCE, params={'limit': 1111}, api='private')["accounts_filtered"]
        return [
            {
                'symbol': sym['currency'],
                'available': sym['balance'],
                'locked': sym['locked']
            } for sym in resp
        ]

    def sign_request(self, path, api='public', method=GET, params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = BASE_URL + path
        if api == 'private':
            nonce = round(time.time() * 1000)
            params.update({'tonce': nonce})
            params.update({'access_key': url_encode(self.__api_key)})
            o = OrderedDict(sorted(params.items()))
            params = {}
            for k in sorted(o):
                params.update({k: o[k]})
            query = _url_encode.urlencode(params)
            message = f'{method}|{path}|{query}'
            signature = hmac_val(message.encode(), self.__api_secret.encode(), hashlib.sha256)
            url += "?" + query + '&signature=' + signature
        else:
            url = generate_path_from_params(params, url)
        return {'url': url, 'method': method, 'body': body, 'headers': {}}

    @no_errors
    def fetch_order_book(self, refid, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": refid,
                  'bids_limit': limit if limit else 50,
                  'asks_limit': limit if limit else 50}
        resp = self._api_call(endpoint=ORDER_BOOK, params=params, api='public')
        while not resp:
            time.sleep(.15)
            resp = self._api_call(endpoint=ORDER_BOOK, params=params, api='public')

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

    @private
    @force_result
    def create_order(self, refid, side, price, volume):
        params = {
            'market': refid,
            'side': side,
            'volume': volume,
            'price': price,
        }
        return self._api_call(endpoint=CREATE_ORDER, params=params, api='private', method='POST')

    def parse_created_order(self, raw_created_order):
        return {
            'refid': raw_created_order['market'],
            'order_id': raw_created_order['id'],
            'status': raw_created_order['state'],
            'side': raw_created_order['side'].lower(),
            'price': raw_created_order['price'],
            'volume': raw_created_order['volume'],
            'executed_volume': raw_created_order['executed_volume'],
            'created': to_database_time(raw_created_order['created_at']),
            'modified': to_database_time(raw_created_order['created_at'])
        }

    @private
    @force_result
    def cancel_order(self, order_id):
        params = {
            'id': int(order_id)
        }
        return self._api_call(endpoint=DELETE_ORDER, params=params, api='private', method='GET')

    def parse_canceled_order(self, raw_response):
        if 'id' in raw_response.keys():
            return True
        return False

    @private
    @force_result
    def fetch_order_status(self, order_id) -> dict:
        params = {
            'id': order_id
        }
        return self._api_call(endpoint=STATUS_ORDER, params=params, api='private', method='GET')

    def parse_order_status(self, raw_order_status) -> dict:
        return {
            'refid': raw_order_status['market'],
            'order_id': raw_order_status['id'],
            'status': raw_order_status['state'],
            'side': raw_order_status['side'],
            'price': raw_order_status['price'],
            'volume': raw_order_status['volume'],
            'executed_volume': raw_order_status['executed_volume'],
            'created': to_database_time(raw_order_status['created_at']),
            'modified': to_database_time(time.time())
        }
