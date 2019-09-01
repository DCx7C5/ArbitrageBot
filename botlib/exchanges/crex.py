import base64
import hashlib
import json
import re
import time

from botlib.exchanges.baseclient import BaseClient
from botlib.sql_functions import get_symbols_for_exchange_sql


BALANCE = "balance"
PLACE_ORDER = "placeOrder"
TICKERS = "tickers"
ORDER_BOOK = "orderBook"
INSTRUMENTS = 'instruments'
STATUS_ORDER = "orderStatus"
DELETE_ORDER = "cancelOrdersById"

# REQUEST HEADER VARIABLES
X_API_SIGN = 'X-CREX24-API-SIGN'
X_API_KEY = 'X-CREX24-API-KEY'
X_API_NONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

# API TYPE
PRIVATE = "PRIVATE"
PUBLIC = "PUBLIC"

BASE_URL = "https://api.crex24.com"


class CrexClient(BaseClient):

    def __init__(self, api_key, api_secret, calls_per_second=6):
        BaseClient.__init__(self)
        self.name = 'Crex24'
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second
        self.logger.debug(f'{self.name} initialized')

    def sign_data_for_prv_api(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = '/v2/' + api + '/' + self.implode_params(path, params)
        query = self.omit(params, re.findall(r'{([\w-]+)}', path))
        if method == 'GET':
            if query:
                request += '?' + self.url_encode(query)
        url = BASE_URL + request
        if (api == 'trading') or (api == 'account'):
            nonce = round(time.time() * 1000000)
            secret = base64.b64decode(self._api_secret)
            auth = request + str(nonce)
            headers = {'X-CREX24-API-KEY': self._api_key, 'X-CREX24-API-NONCE': str(nonce)}
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                body = json.dumps(params, separators=(',', ':'))
                auth += body
            signature = base64.b64encode(self.hmac(auth.encode(), secret, hashlib.sha512, 'binary'))
            headers['X-CREX24-API-SIGN'] = signature.decode()
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def get_order_book(self, refid, limit=None) -> tuple:
        params = {"instrument": refid}
        if limit:
            params['limit'] = limit
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['buyLevels']],\
               [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['sellLevels']]

    def update_balance(self) -> None:
        response = self.api_call(endpoint=BALANCE, params={}, api='account')
        exch_symbols = [s for s in get_symbols_for_exchange_sql(self.name)] + [("BTC", "BTC")]
        for a in exch_symbols:
            for i in response:
                if i['currency'] == a[0]:
                    with self.lock:
                        self.balances.update(
                            {a[1]: i['available']}
                        )

    def update_min_order_vol(self) -> None:
        response = self.api_call(endpoint=INSTRUMENTS, params={}, api='public')
        for i in response:
            if i['symbol'] in self.balances.keys():
                self.min_order_vol.update({i['symbol']: float(i['minVolume'])})

    def create_order(self, refid, side, price, volume):
        params = {'instrument': refid, 'side': side, 'price': price, 'volume': volume}
        response = self.api_call(endpoint=PLACE_ORDER, params=params, api='trading', method="POST")
        return response['id']

    def get_order_status(self, order_id):
        return self.api_call(endpoint=STATUS_ORDER, params={'id': order_id}, api='trading')[0]

    def cancel_order(self, order_id):
        return self.api_call(endpoint=DELETE_ORDER, params={'id': order_id}, api='trading', method="POST")[0]
