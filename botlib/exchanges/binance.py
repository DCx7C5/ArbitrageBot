from botlib.exchanges.baseclient import BaseClient
import urllib.parse as _url_encode

# API ENDPOINTS

ORDER_BOOK = 'depth'
ACCOUNT = 'account'


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

    PUBLIC_API = 'https://api.binance.com/api/v1'
    PRIVATE_API = 'https://api.binance.com/api/v3'
    WAPI = 'https://api.binance.com/api/v3'
    WITHDRAW_API_URL = 'https://api.binance.com/wapi'
    MARGIN_API_URL = 'https://api.binance.com/sapi'

    PUBLIC = {
        'get': ['ping', 'time', 'depth', 'trades', 'aggTrades', 'historicalTrades', 'klines', 'exchangeInfo'],
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

    def sign(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        url = self.PUBLIC_API
        url += '/' + path
        if api == 'wapi':
            url += '.html'
        user_data_stream = (path == 'userDataStream')
        if path == 'historicalTrades':
            headers = {'X-MBX-APIKEY': self._api_key}
        elif user_data_stream:
            body = _url_encode.urlencode(params)
            headers = {'X-MBX-APIKEY': self._api_key, 'Content-Type': 'application/x-www-form-urlencoded'}
        if (api == 'private') or (api == 'wapi' and path != 'systemStatus'):
            print(12)
            query = _url_encode.urlencode(self.extend({
                'timestamp': int(self.nonce() * 1000),
                'recvWindow': 5000}, params))
            print(self.nonce())
            signature = self.hmac(self.encode(query), self.encode(self._api_secret))
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

    def request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        response = self.__fetch2(path, api, method, params, headers, body)
        # a workaround for {"code":-2015,"msg":"Invalid API-key, IP, or permissions for action."}
        if (api == 'private') or (api == 'wapi'):
            self.options['hasAlreadyAuthenticatedSuccessfully'] = True
        return response

    def get_order_book(self, refid, limit=None):
        params = {"symbol": refid,
                  'limit': limit if limit else 500}
        resp = self.api_call(endpoint=ORDER_BOOK, params=params, api='public')
        return [[x[0], round(float(x[1]), 10)] for x in resp['bids']],\
               [[x[0], round(float(x[1]), 10)] for x in resp['asks']]

    def get_balance(self, symbol):

        print(self.api_call(endpoint=ACCOUNT, params=None, api='private'))
