import base64
import hashlib
import json
import re
import time

from botlib.api_client.client_utils import implode_params, omit, url_encode, hmac_val, precision_from_string, \
    to_database_time
from botlib.api_client.baseclient import BaseClient
from botlib.sql_functions import get_key_and_secret_sql, get_one_symbol_from_exchange_sql
from botlib.api_client.client_utils import no_errors, force_result, private

BALANCE = "balance"
CREATE_ORDER = "placeOrder"
TICKERS = "tickers"
ORDER_BOOK = "orderBook"
INSTRUMENTS = 'instruments'
STATUS_ORDER = "orderStatus"
DELETE_ORDER = "cancelOrdersById"
CURRENCIES = "currencies"
DEPOSIT_ADDRESS = "depositAddress"
FEES = "tradeFee"
WITHDRAW = "withdraw"

# REQUEST HEADER VARIABLES
X_API_SIGN = 'X-CREX24-API-SIGN'
X_API_KEY = 'X-CREX24-API-KEY'
X_API_NONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

BASE_URL = "https://api.crex24.com"

PUBLIC = 'public'

ORDER_STATES = {
    'new': ['submitting', 'unfilledActive', 'waiting'],
    'all_filled': ['filled'],
    'partially_filled': ['partiallyFilledActive'],
    'canceled': ['unfilledCancelled', 'partiallyFilledCancelled']
}


class CrexClient(BaseClient):
    """Crex24 Exchange API Client"""

    name = "Crex24"
    rate_limit = 1.0 / 6
    maker_fees = 0.001
    taker_fees = 0.001
    trading_fee_type = 'percentage'
    transaction_fee_type = ''
    __api_key, __api_secret = get_key_and_secret_sql(name)

    @force_result
    def parse_all_market_information(self):
        return [
            {
                'refid': i['symbol'],
                'base_asset': i['baseCurrency'],
                'quote_asset': i['quoteCurrency'],
                'minimum_order_volume': i['minVolume'],
                'price_precision': precision_from_string(str(i['tickSize'])),
                'order_volume_precision': precision_from_string(str(i['minVolume'])),
                'order_volume_step_size': round(float(i['minVolume']), precision_from_string(str(i['minVolume']))),
                'minimum_order_cost': 0.0000001

            } for i in self._api_call(endpoint=INSTRUMENTS, params={}, api=PUBLIC)
        ]

    @private
    @force_result
    def fetch_all_balances(self):
        response = self._api_call(endpoint=BALANCE, params={'nonZeroOnly': 'false'}, api='account')
        return [{'available': i['available'], 'locked': i['reserved'], 'symbol': i['currency']} for i in response]

    def sign_request(self, path, api=PUBLIC, method='GET', params=None, headers=None, body=None):
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
            secret = base64.b64decode(self.__api_secret)
            auth = request + str(nonce)
            headers = {'X-CREX24-API-KEY': self.__api_key, 'X-CREX24-API-NONCE': str(nonce)}
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                body = json.dumps(params, separators=(',', ':'))
                auth += body
            signature = base64.b64encode(hmac_val(auth.encode(), secret, hashlib.sha512, 'binary'))
            headers['X-CREX24-API-SIGN'] = signature.decode()
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    @no_errors
    def fetch_order_book(self, refid, limit=None) -> tuple:
        params = {"instrument": refid}
        if limit:
            params['limit'] = limit
        resp = self._api_call(endpoint=ORDER_BOOK, params=params, api=PUBLIC)
        return [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['buyLevels']],\
               [[round(float(x['price']), 10), round(float(x['volume']), 10)] for x in resp['sellLevels']]

    @private
    @force_result
    def create_order(self, refid: str, side: str, price: float, volume: float):
        params = {
            'instrument': refid,
            'side': side,
            'type': 'limit',
            'timeInForce': 'GTC',
            'volume': volume,
            'price': price,
        }
        return self._api_call(endpoint=CREATE_ORDER, params=params, api='private', method='POST')

    def parse_created_order(self, raw_created_order):
        created = to_database_time(raw_created_order['timestamp'])
        if raw_created_order['lastUpdate'] is not None:
            last_update = to_database_time(raw_created_order['lastUpdate'])
        else:
            last_update = created
        return {
            'refid': raw_created_order['symbol'],
            'order_id': int(raw_created_order['id']),
            'status': raw_created_order['status'],
            'side': raw_created_order['side'].lower(),
            'price': float(raw_created_order['price']),
            'volume': float(raw_created_order['volume']),
            'executed_volume': float(raw_created_order['origQty']) - float(raw_created_order['remainingVolume']),
            'created': created,
            'modified': last_update
        }

    @private
    @force_result
    def cancel_order(self, order_id):
        params = {
            'ids': [int(order_id)]
        }
        return self._api_call(endpoint=DELETE_ORDER, params=params, api='private', method='POST')

    def parse_canceled_order(self, raw_response):
        if len(raw_response) != 1:
            return True
        return False

    @private
    @force_result
    def fetch_order_status(self, order_id, refid=None):
        params = {
            'id': int(order_id)
        }
        return self._api_call(endpoint=STATUS_ORDER, params=params, api='private', method='GET')

    def parse_order_status(self, raw_order_status):
        created = to_database_time(raw_order_status['timestamp'])
        if raw_order_status['lastUpdate'] is not None:
            last_update = to_database_time(raw_order_status['lastUpdate'])
        else:
            last_update = created
        return {
            'refid': raw_order_status['instrument'],
            'side': raw_order_status['side'].lower(),
            'order_id': int(raw_order_status['id']),
            'status': raw_order_status['status'],
            'volume': raw_order_status['volume'],
            'executed_volume': float(raw_order_status['origQty']) - float(raw_order_status['remainingVolume']),
            'created': created,
            'modified': last_update,
        }

    @private
    @force_result
    def fetch_deposit_address(self, refid) -> dict:
        symbol = get_one_symbol_from_exchange_sql(self.name, refid)
        params = {
            'currency': symbol
        }
        return self._api_call(endpoint=DEPOSIT_ADDRESS, params=params, api='account', method="GET")

    def parse_deposit_address(self, raw_response) -> str:
        return raw_response['address']

    @private
    @force_result
    def create_withdrawal(self, refid, amount, address):
        symbol = get_one_symbol_from_exchange_sql(self.name, refid)
        params = {
            'currency': symbol,
            'amount': amount,
            'address': address
        }
        return self._api_call(endpoint=WITHDRAW, params=params, api='account', method="POST")

    def parse_withdrawal(self, raw_response):
        return {
            'withdrawal_id': raw_response["id"],
            'asset': raw_response['currency'],
            'send_to': raw_response['address'],
            'amount': raw_response['amount'],
            'fee': raw_response['fee'] if raw_response['fee'] is not None else None,
            'tx_id': raw_response['txId'] if raw_response['txId'] is not None else None,
            'created': to_database_time(raw_response['createdAt']),
            'processed': to_database_time(raw_response['processedAt']) if raw_response['processedAt'] is not None else None,
            'status': raw_response['status']
        }
