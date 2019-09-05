import time
import urllib.parse as _url_encode

from botlib.exchanges.baseclient import BaseClient
from botlib.sql_functions import get_symbols_for_exchange_sql, get_refid_from_order_id

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

    def __init__(self, api_key, api_secret, calls_per_second=15):
        BaseClient.__init__(self)
        self.name = 'Binance'
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second
        self.lot_size = {}
        self.logger.debug(f'{self.name} initialized')

    def sign_request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = BASE_URL
        url += '/' + path
        if api == 'wapi':
            url = WAPI
            url += '/' + path
        if api == 'private':
            url = PRIVATE_API
            url += '/' + path
        if api == 'public':
            url = PUBLIC_API
            url += '/' + path
        user_data_stream = (path == 'userDataStream')
        if path == 'historicalTrades':
            headers = {'X-MBX-APIKEY': self._api_key}
        elif user_data_stream:
            body = _url_encode.urlencode(params)
            headers = {'X-MBX-APIKEY': self._api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        if (api == 'private') or (api == 'wapi' and path != 'systemStatus'):
            nonce = int(time.time() * 1000)
            query = _url_encode.urlencode(self.extend({
                'timestamp': nonce,
                'recvWindow': 5000}, params))
            signature = self.hmac(query.encode(), self._api_secret.encode())
            query += '&' + 'signature=' + signature
            headers = {'X-MBX-APIKEY': self._api_key}
            if (method == 'GET') or (method == 'DELETE') or (api == 'wapi'):
                url += '?' + query
            else:
                body = query
                headers['Content-Type'] = 'application/x-www-form-urlencoded'
        else:
            if not user_data_stream:
                if params:
                    url += '?' + self.url_encode(params)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def get_order_book(self, refid, limit=None):
        params = {"symbol": refid, 'limit': limit if limit else 500}
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['bids']],\
               [[round(float(x[0]), 10), round(float(x[1]), 10)] for x in resp['asks']]

    def update_balance(self):
        response = self.api_call(endpoint=ACCOUNT, params={}, api='private')
        exch_symbols = [s for s in get_symbols_for_exchange_sql(self.name)] + [('BTC', "BTC")]
        for a in exch_symbols:
            for i in response['balances']:
                if i['asset'] == a[0]:
                    with self.lock:
                        self.balances.update(
                            {a[1]: i['free']}
                        )

    def update_min_order_vol(self):
        response = self.api_call(endpoint=INFO, params={}, api='public')
        for i in response['symbols']:
            if i['symbol'] in self.balances.keys():
                with self.lock:
                    self.min_order_vol.update({i['symbol']: [x for x in i['filters'] if x['filterType'] == 'LOT_SIZE'][0]['minQty']})

    def create_order(self, refid, side, price, volume):
        counter = 0
        if side == "buy":
            side = "BUY"
        elif side == "sell":
            side = "SELL"
        mov = str(self.get_min_order_vol(refid))
        before_comma = int(mov.split(".")[0])
        after_comma = mov.split(".")[1]
        for i in after_comma:
            counter += 1
            if int(i) == 1:
                break
        if before_comma == 1:
            _volume = round(volume, 0)
        else:
            _volume = round(volume, counter)
        params = {'symbol': refid, 'side': side, "timeInForce": "GTC", 'type': "LIMIT", 'price': price, 'quantity': _volume}
        response = self.api_call(endpoint=CREATE_ORDER, params=params, api='private', method="POST")
        return response["orderId"]

    def get_order_status(self, order_id):
        symbol = get_refid_from_order_id(order_id)
        return self.api_call(endpoint=STATUS_ORDER, params={'symbol': symbol, 'orderId': order_id}, api='private')

    def cancel_order(self, order_id):
        symbol = get_refid_from_order_id(order_id)
        return self.api_call(endpoint=STATUS_ORDER, params={'symbol': symbol, 'orderId': order_id}, api='private')
