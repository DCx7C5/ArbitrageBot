import time
import urllib.parse as _url_encode

from botlib.bot_utils import extend, hmac_val, url_encode
from botlib.exchanges.baseclient import BaseClient
from botlib.sql_functions import get_refid_from_order_id, get_deposit_address

# API ENDPOINTS

ORDER_BOOK = 'depth'
ACCOUNT = 'account'
INFO = 'exchangeInfo'
GET_ADDRESS = 'depositAddress'
SEND_TO_ADDRESS = ''
CREATE_ORDER = 'order'
STATUS_ORDER = 'order'

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


class BinanceClient(BaseClient):
    """Binance Exchange API Client"""

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

        super().__init__()
        self.name = 'Binance'
        self.rate_limit = 1.0 / 15
        self.balances_keys = 'symbol'

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
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
            headers = {'X-MBX-APIKEY': self.api_key}
        elif user_data_stream:
            body = _url_encode.urlencode(params)
            headers = {'X-MBX-APIKEY': self.api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        if (api == 'private') or (api == 'wapi' and path != 'systemStatus'):
            nonce = int(time.time() * 1000)
            query = _url_encode.urlencode(extend({
                'timestamp': nonce,
                'recvWindow': 5000}, params))
            signature = hmac_val(query.encode(), self.api_secret.encode())
            query += '&' + 'signature=' + signature
            headers = {'X-MBX-APIKEY': self.api_key}
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

    def get_order_book(self, refid, limit=None):
        params = {"symbol": refid, 'limit': limit if limit else 500}
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['bids']],\
               [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['asks']]

    def update_all_markets(self):
        response = self.api_call(endpoint=INFO, params={}, api='public')
        for setting in self.markets.keys():
            for i in response['symbols']:
                self.markets[setting].update({i['symbol']: {}})

    def update_all_balances(self):
        response = self.api_call(endpoint=ACCOUNT, params={}, api='private')
        for bal in response['balances']:
            self.balances.update({bal['asset']: {'available': bal['free'], 'locked': bal['locked']}})

    def update_min_order_vol(self):
        response = self.api_call(endpoint=INFO, params={}, api='public')
        for i in response['symbols']:
            if i['symbol'] in self.balances.keys():
                with self.lock:
                    self.min_order_vol.update({i['symbol']: [x for x in i['filters'] if x['filterType'] == 'LOT_SIZE'][0]['minQty']})

    def create_order(self, refid, side, price, volume) -> dict:
        if side == "buy":
            side = "BUY"
        elif side == "sell":
            side = "SELL"
        mov = str(self.get_min_order_vol(refid))
        before_comma = mov.split(".")[0]
        after_comma = mov.split(".")[1]
        if "1" in before_comma:
            _volume = int(round(volume / before_comma))
        else:
            counter = 0
            for i in after_comma:
                counter += 1
                if int(i) == 1:
                    break
            _volume = round(float(volume), counter)
        params = {'symbol': refid, 'side': side, "timeInForce": "GTC", 'type': "LIMIT", 'price': price, 'quantity': _volume}
        response = self.api_call(endpoint=CREATE_ORDER, params=params, api='private', method="POST")
        status_resp = response['status']
        if status_resp == 'FILLED':
            status = "done"
        elif status_resp == 'PARTIALLY_FILLED':
            status = "partially"
        else:
            status = status_resp
        return {
            'order_id': response['orderId'],
            'refid': refid,
            'status': status,
            'side': side,
            'price': response['price'],
            'volume': response['origQty'],
            'executed_volume': response['executedQty']
        }

    def get_order_status(self, order_id):
        symbol = get_refid_from_order_id(order_id)
        response = self.api_call(endpoint=STATUS_ORDER, params={'symbol': symbol, 'orderId': order_id}, api='private')

        return {
            'status': response['status'],
            'executed_volume': response["executedQty"]
        }

    def cancel_order(self, order_id):
        symbol = get_refid_from_order_id(order_id)
        response = self.api_call(endpoint=STATUS_ORDER, params={'symbol': symbol, 'orderId': order_id}, api='private')
        if response["status"] == "CANCELED":
            return True
        return False

    def update_deposit_address(self, refid):
        # Workaround for Binance deposit addresses
        return get_deposit_address(self.name, refid)
