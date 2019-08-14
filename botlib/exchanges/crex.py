import base64
import concurrent.futures
import hmac
import json
import time
import urllib.parse

from hashlib import sha512
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASE_URL = "https://api.crex24.com"


# API ENDPOINTS
BALANCE = "/v2/account/balance"
PLACE_ORDER = "/v2/trading/placeOrder"
TICKERS = "/v2/public/tickers"
ORDER_BOOK = "/v2/public/orderBook"

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


class CrexClient:

    def __init__(self, api_key, api_secret, calls_per_second=6):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    @staticmethod
    def _generate_path(params, endpoint):
        params_string = "?"
        for p in params:
            params_string += f'{p}={params[p]}' + "&"
        return f'{endpoint}{params_string[:-1]}'

    def _generate_hash_signature(self, msg_string):
        return base64.b64encode(hmac.new(key=self.api_secret,
                                         msg=msg_string,
                                         digestmod=sha512).digest())

    def _api_call(self, method: str,
                  endpoint: str,
                  params: dict = None,
                  private=False):
        """
        BASE FUNCTION FOR MAKING API CALLS TO GRAVIEX
        """
        if not params:
            params = {}

        path = self._generate_path(params, endpoint)

        nonce = round(time.time() * 1000000)

        key = base64.b64decode(self.api_secret)

        url = f'{BASE_URL}{path}'
        print(url)
        request = Request(url)

        if method == POST:
            data = json.dumps(params, separators=(',', ':'))
            message = str.encode(path + str(nonce) + data, "utf-8")
            request.data = str.encode(data, "utf-8")
            request.add_header(CONTENT_LENGTH, len(data))
        else:
            message = str.encode(path + str(nonce), "utf-8")

        hmacvar = hmac.new(key, message, sha512)

        signature = base64.b64encode(hmacvar.digest())

        request.method = method
        request.add_header(X_API_KEY, self.api_key)
        request.add_header(X_API_NONCE, nonce)
        request.add_header(X_API_SIGN, signature)

        try:
            response = urlopen(request)
            print(response)
        except HTTPError as e:
            response = e
        return json.loads(bytes.decode(response.read()))

    def get_balance(self, currency=None):
        params = {"currency": currency} if currency else {}
        return self._api_call(GET, BALANCE, params, private=True)

    def create_order(self, refid, side, amount, price, order_type=None):
        params = {"instrument": refid, "side": side, "volume": amount}
        if order_type != "stop_limit":
            params.update({"price": price})
        if order_type is not None:
            params.update({"type": order_type})
        return self._api_call(POST, PLACE_ORDER, params, private=True)

    def get_order_book(self, refid, limit=None):
        params = {"instrument": refid}
        if limit:
            params['limit'] = limit
        resp = self._api_call(endpoint=ORDER_BOOK, method=GET, params=params, private=False)
        return [(x['price'], x['volume']) for x in resp['buyLevels']], [(x['price'], x['volume']) for x in resp['sellLevels']]

