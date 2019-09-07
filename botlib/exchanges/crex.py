import base64
import hashlib
import json
import re
import time

from botlib.bot_utils import implode_params, omit, url_encode, hmac_val
from botlib.exchanges.baseclient import BaseClient
from botlib.sql_functions import get_symbols_for_exchange_sql


BALANCE = "balance"
PLACE_ORDER = "placeOrder"
TICKERS = "tickers"
ORDER_BOOK = "orderBook"
INSTRUMENTS = 'instruments'
STATUS_ORDER = "orderStatus"
DELETE_ORDER = "cancelOrdersById"
CURRENCIES = "currencies"
DEPOSIT_ADDRESS = "depositAddress"

# REQUEST HEADER VARIABLES
X_API_SIGN = 'X-CREX24-API-SIGN'
X_API_KEY = 'X-CREX24-API-KEY'
X_API_NONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

BASE_URL = "https://api.crex24.com"


class CrexClient(BaseClient):
    """Crex24 Exchange API Client"""

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        super().__init__()
        self.name = 'Crex24'
        self.rate_limit = 1.0 / 6

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = '/v2/' + api + '/' + implode_params(path, params)
        query = omit(params, re.findall(r'{([\w-]+)}', path))
        if method == 'GET':
            if query:
                request += '?' + url_encode(query)
        url = BASE_URL + request
        if (api == 'trading') or (api == 'account'):
            nonce = round(time.time() * 1000000)
            secret = base64.b64decode(self.api_secret)
            auth = request + str(nonce)
            headers = {'X-CREX24-API-KEY': self.api_key, 'X-CREX24-API-NONCE': str(nonce)}
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                body = json.dumps(params, separators=(',', ':'))
                auth += body
            signature = base64.b64encode(hmac_val(auth.encode(), secret, hashlib.sha512, 'binary'))
            headers['X-CREX24-API-SIGN'] = signature.decode()
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def update_all_markets(self):
        response = self.api_call(endpoint=INSTRUMENTS, params={}, api='public')
        for i in response:
            self.markets.update({i['symbol']: {}})

    def update_all_balances(self):
        response = self.api_call(endpoint=BALANCE, params={'nonZeroOnly': 'false'}, api='account')
        for i in response:
            self.balances.update({i['currency']: {'available': i['available'], 'locked': i['reserved']}})

    def get_order_book(self, refid, limit=None) -> tuple:
        params = {"instrument": refid}
        if limit:
            params['limit'] = limit
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['buyLevels']],\
               [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['sellLevels']]

    def update_min_order_vol(self) -> None:
        response = self.api_call(endpoint=INSTRUMENTS, params={}, api='public')
        for i in response:
            if i['symbol'] in self.balances.keys():
                self.min_order_vol.update({i['symbol']: float(i['minVolume'])})

    def create_order(self, refid, side, price, volume) -> dict:
        min_order_volume = str(self.get_min_order_vol(refid))
        before_comma = min_order_volume.split(".")[0]
        after_comma = min_order_volume.split(".")[1]
        if "1" in before_comma:
            _volume = int(round(float(volume) / float(before_comma)))
        else:
            _volume = round(float(min_order_volume), len(after_comma))
        params = {'instrument': refid, 'side': side, 'price': price, 'volume': volume}
        response = self.api_call(endpoint=PLACE_ORDER, params=params, api='trading', method="POST")
        exec_volume = volume - response['remainingVolume']
        if response['status'] == "filled":
            status = "done"
        else:
            status = response['status']
        return {
            'order_id': response['id'],
            'refid': refid,
            'status': status,
            'side': side,
            'price': response['price'],
            'volume': response['volume'],
            'executed_volume': exec_volume
        }

    def get_order_status(self, order_id):
        response = self.api_call(endpoint=STATUS_ORDER, params={'id': order_id}, api='trading')[0]
        exec_volume = response['volume'] - response['remainingVolume']
        if response['status'] == "filled":
            status = "done"
        else:
            status = response['status']
        return {
            'order_id': response['id'],
            'status': status,
            'executed_volume': exec_volume
        }

    def cancel_order(self, order_id):
        response = self.api_call(endpoint=DELETE_ORDER, params={'ids': [order_id]}, api='trading', method="POST")[0]
        if order_id in response:
            return True
        return False

    def update_deposit_address(self, refid):
        symbol = self.markets[refid]['symbol']
        response = self.api_call(endpoint=DEPOSIT_ADDRESS, params={'currency': symbol}, api='trading', method="POST")
        print(response)
