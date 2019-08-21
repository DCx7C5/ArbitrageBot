import base64
import hashlib
from botlib.exchanges.baseclient import BaseClient

# API ENDPOINTS
BALANCE = "/account/balance"
PLACE_ORDER = "/placeOrder"
TICKERS = "/tickers"
ORDER_BOOK = "/orderBook"

# REQUEST HEADER VARIABLES
X_API_SIGN = 'X-CREX24-API-SIGN'
X_API_KEY = 'X-CREX24-API-KEY'
X_API_NONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

# REQUEST METHODS
POST = "POST"
GET = "GET"

# API TYPE
PRIVATE = "PRIVATE"
PUBLIC = "PUBLIC"


class CrexClient(BaseClient):

    BASE_URL = "https://api.crex24.com"

    def __init__(self, api_key, api_secret, calls_per_second=6):
        BaseClient.__init__(self)
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second
        self._last_call = None

    def sign(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = '/v2/' + api + '/' + self.implode_params(path, params)
        query = self.omit(params, self.extract_params(path))
        if method == 'GET':
            if query:
                request += '?' + self.url_encode(query)
        url = self.BASE_URL + request
        if (api == 'trading') or (api == 'account'):
            nonce = str(self.nonce())
            secret = base64.b64decode(self._api_secret)
            auth = request + nonce
            headers = {
                'X-CREX24-API-KEY': self._api_key,
                'X-CREX24-API-NONCE': nonce,
            }
            if method == 'POST':
                headers['Content-Type'] = 'application/json'
                body = self.json(params)
                auth += body
            signature = base64.b64encode(self.hmac(self.encode(auth), secret, hashlib.sha512, 'binary'))
            headers['X-CREX24-API-SIGN'] = self.decode(signature)
        return {'url': url, 'method': method, 'body': body, 'headers': headers}

    def get_order_book(self, refid, limit=None):
        params = {"instrument": refid}
        if limit:
            params['limit'] = limit
        resp = self.api_call(endpoint=ORDER_BOOK, params=params)
        return [[x['price'], round(float(x['volume']), 10)] for x in resp['buyLevels']],\
               [[x['price'], round(float(x['volume']), 10)] for x in resp['sellLevels']]

    def get_balance(self, symbol):
        params = {"instrument": symbol}
        print(self.api_call(endpoint=ORDER_BOOK, params=params))