import time
import urllib.parse as _url_encode

from botlib.api_client.client_utils import extend, hmac_val, url_encode, to_database_time
from botlib.api_client.baseclient import BaseClient, private, no_errors, force_result

# API ENDPOINTS
from botlib.sql_functions import get_key_and_secret_sql

ORDER_BOOK = 'depth'
ACCOUNT = 'account'
INFO = 'exchangeInfo'
GET_ADDRESS = 'depositAddress'
CREATE_ORDER = 'order'
STATUS_ORDER = 'order'
CANCEL_ORDER = 'order'

# REQUEST METHODS
POST = "POST"
GET = "GET"

# HTTP HEADERS
ACCEPT = 'Accept'
USER_AGENT = 'User-Agent'
X_MBX_APIKEY = 'X-MBX-APIKEY'
APPL_JSON = 'application/json'
BIN_PYTH = 'binance/python'

IP = "143.204.206.178"  #
PUBLIC_API = f'https://api.binance.com/api/v1'
PRIVATE_API = f'https://api.binance.com/api/v3'
WAPI = f'https://api.binance.com/wapi/v3'
MARGIN_API_URL = f'https://api.binance.com/sapi/v3'
BASE_URL = "https://api.binance.com"

PUBLIC = {
    'get': ['depth', 'trades', 'aggTrades', 'exchangeInfo'],
    'put': ['userDataStream'],
    'post': ['userDataStream'],
    'delete': ['userDataStream']
}
PRIVATE = {
    'get': ['order', 'openOrders', 'allOrders', 'account', 'myTrades', 'depositAddress'],
    'post': ['order', 'order/test'],
    'delete': ['order']
}

ORDER_STATES = {
    'new': ['NEW'],
    'all_filled': ['FILLED'],
    'partially_filled': ['PARTIALLY_FILLED'],
    'canceled': ['CANCELED', 'REJECTED', "EXPIRED"]
}


class BinanceClient(BaseClient):
    """Binance Exchange API Client"""

    _name = "Binance"
    _rate_limit = 1.0 / 7
    _maker_fees = 0.1
    _taker_fees = 0.1
    __api_key, __api_secret = get_key_and_secret_sql(_name)

    @force_result
    def parse_all_market_information(self):
        data = []
        markets = self._api_call(endpoint=INFO, params={}, api='public')['symbols']
        for market in markets:
            minimum_order_volume = None
            order_volume_step_size = None
            minimum_order_cost = None
            symbol = market["symbol"]
            base_asset = market["baseAsset"]
            quote_asset = market["quoteAsset"]
            order_volume_precision = market["baseAssetPrecision"]
            price_precision = market["quotePrecision"]
            for _filter in market['filters']:
                if _filter['filterType'] == "LOT_SIZE":
                    minimum_order_volume = _filter["minQty"]
                    order_volume_step_size = _filter["stepSize"]
                elif _filter['filterType'] == "MIN_NOTIONAL":
                    minimum_order_cost = _filter['minNotional']
            data.append({
                'refid': symbol,
                'base_asset': base_asset,
                'quote_asset': quote_asset,
                'order_volume_precision': order_volume_precision,
                'price_precision': price_precision,
                'minimum_order_volume': round(float(minimum_order_volume), order_volume_precision),
                'order_volume_step_size': round(float(order_volume_step_size), order_volume_precision),
                'minimum_order_cost': minimum_order_cost

            })
        return data

    @private
    @force_result
    def fetch_all_balances(self):
        response = self._api_call(endpoint=ACCOUNT, params={}, api='private')['balances']
        return [{'symbol': bal['asset'], 'available': bal['free'], 'locked': bal['locked']} for bal in response]

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None) -> dict:
        if params is None:
            params = {}
        url = BASE_URL
        url += '/' + path
        if api == 'public':
            url = PUBLIC_API
            url += '/' + path
        elif api == 'private':
            url = PRIVATE_API
            url += '/' + path
        elif api == 'wapi':
            url = WAPI
            url += '/' + path
        user_data_stream = (path == 'userDataStream')
        if path == 'historicalTrades':
            headers = {'X-MBX-APIKEY': self.__api_key}
        elif user_data_stream:
            body = _url_encode.urlencode(params)
            headers = {'X-MBX-APIKEY': self.__api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        if (api == 'private') or (api == 'wapi' and path != 'systemStatus'):
            nonce = int(time.time() * 1000)
            query = _url_encode.urlencode(extend({
                'timestamp': nonce,
                'recvWindow': 5000}, params))
            signature = hmac_val(query.encode(), self.__api_secret.encode())
            query += '&' + 'signature=' + signature
            headers = {'X-MBX-APIKEY': self.__api_key}
            if (method == 'GET') or (method == 'DELETE') or (api == 'wapi'):
                url += '?' + query
            else:
                body = query
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            if not user_data_stream:
                if params:
                    url += '?' + url_encode(params)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    @no_errors
    def fetch_order_book(self, refid, limit=None):
        params = {"symbol": refid, 'limit': limit if limit else 500}
        resp = self._api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['bids']],\
               [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['asks']]

    @private
    @force_result
    def create_order(self, refid: str, side: str, price: float, volume: float):
        params = {
            'symbol': refid,
            'side': side.upper(),
            'type': 'LIMIT',
            'timeInForce': 'GTC',
            'quantity': volume,
            'price': price,
            'newOrderRespType': 'RESULT'
        }
        return self._api_call(endpoint=CREATE_ORDER, params=params, api='private', method='POST')

    def parse_created_order(self, raw_created_order):

        return {
            'refid': raw_created_order['symbol'],
            'order_id': raw_created_order['orderId'],
            'status': raw_created_order['status'],
            'side': raw_created_order['side'].lower(),
            'price': raw_created_order['price'],
            'volume': raw_created_order['origQty'],
            'executed_volume': raw_created_order['executedQty'],
            'created': to_database_time(raw_created_order['transactTime']),
            'modified': to_database_time(raw_created_order['transactTime'])
        }

    @private
    @force_result
    def cancel_order(self, refid, order_id):
        params = {
            'symbol': refid,
            'orderId': order_id
        }
        return self._api_call(endpoint=CANCEL_ORDER, params=params, api='private', method='DELETE')

    def parse_canceled_order(self, raw_response):
        if raw_response['status'] == "CANCELED":
            return True
        return False

    @private
    @force_result
    def fetch_order_status(self, refid, order_id):
        params = {
            'symbol': refid,
            'orderId': order_id
        }
        return self._api_call(endpoint=STATUS_ORDER, params=params, api='private', method='GET')

    def parse_order_status(self, raw_order_status):
        return {
            'refid': raw_order_status['symbol'],
            'order_id': raw_order_status['orderId'],
            'status': raw_order_status['status'],
            'side': raw_order_status['side'].lower(),
            'price': raw_order_status['price'],
            'volume': raw_order_status['origQty'],
            'executed_volume': raw_order_status['executedQty'],
            'created': to_database_time(raw_order_status['time']),
            'modified': to_database_time(raw_order_status['updateTime'])
        }
