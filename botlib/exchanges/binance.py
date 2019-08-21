from botlib.exchanges.baseclient import BaseClient
import urllib.parse as _url_encode

# API ENDPOINTS

ORDER_BOOK = '/depth'

# REQUEST METHODS
POST = "POST"
GET = "GET"

# HTTP HEADERS
ACCEPT = 'Accept'
USER_AGENT = 'User-Agent'
X_MBX_APIKEY = 'X-MBX-APIKEY'
APPL_JSON = 'application/json'
BIN_PYTH = 'binance/python'


class BinanceClient(BaseClient):

    BASE_URL = 'https://api.binance.com/api/v1'
    WITHDRAW_API_URL = 'https://api.binance.com/wapi'
    MARGIN_API_URL = 'https://api.binance.com/sapi'

    PUBLIC = {
        'get': ['ping', 'time', 'depth', 'trades', 'aggTrades', 'historicalTrades', 'klines', 'ticker/24hr',
                'ticker/allPrices', 'ticker/allBookTickers', 'ticker/price', 'ticker/bookTicker', 'exchangeInfo'],
        'put': ['userDataStream'],
        'post': ['userDataStream'],
        'delete': ['userDataStream']
    }

    PRIVATE = {
        'get': ['order', 'openOrders', 'allOrders', 'account', 'myTrades'],
        'post': ['order', 'order/test'],
        'delete': ['order']
    }

    def __init__(self, api_key, api_secret, calls_per_second=15):
        BaseClient.__init__(self)
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second

    def _sign_routine(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = 'https://api.binance.com/api/v1'
        url += '/' + path
        if api == 'wapi':
            url += '.html'
        user_data_stream = (path == 'userDataStream')
        if path == 'historicalTrades':
            headers = {
                'X-MBX-APIKEY': self._api_key,
            }
        elif user_data_stream:
            # v1 special case for userDataStream
            body = _url_encode.urlencode(params)
            headers = {
                'X-MBX-APIKEY': self._api_key,
                'Content-Type': 'application/x-www-form-urlencoded',
            }
        if (api == 'private') or (api == 'wapi' and path != 'systemStatus'):
            query = _url_encode.urlencode(self.extend({
                'timestamp': self.nonce(),
                'recvWindow': self.options['recvWindow']}, params))
            signature = self.hmac(self.encode(query), self.encode(self._api_secret))
            query += '&' + 'signature=' + signature
            headers = {
                'X-MBX-APIKEY': self._api_key,
            }
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
        params = {"symbol": refid,
                  'limit': limit if limit else 500}
        resp = self.api_call_public(path=ORDER_BOOK, params=params)
        return [[x[0], round(float(x[1]), 10)] for x in resp['bids']],\
               [[x[0], round(float(x[1]), 10)] for x in resp['asks']]

