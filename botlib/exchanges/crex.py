import datetime
import base64
import hmac
import json
import threading
import aiohttp
import time
from hashlib import sha512
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASEURL = "https://api.crex24.com"

# API ENDPOINTS
BALANCE = "/v2/account/balance"
PLACEORDER = "/v2/trading/placeOrder"
TICKERS = "/v2/public/tickers"
ORDERBOOK = "/v2/public/orderBook"

# REQUEST HEADER VARIABLES
XAPISIGN = 'X-CREX24-API-SIGN'
XAPIKEY = 'X-CREX24-API-KEY'
XAPINONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

# BALANCE PARAMETERS
CURRENCY = 'currency'

# REQUEST TYPES
GET = 'GET'
POST = 'POST'


# API TYPE
PRIVATE = "PRIVATE"
PUBLIC = "PUBLIC"


def _generate_path(params, endpoint):
    params_string = "?"
    for p in params:
        params_string += f'{p}={params[p]}' + "&"
    return f'{endpoint}{params_string[:-1]}'


def _translate_coin_to_instrument(coin):
    return coin.upper() + "-" + "BTC"


class CrexClien:

    def __init__(self, api_key, api_secret, calls_per_second=6):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None
        self._wait_lock = threading.RLock()

    def _api_call(self, method: str,
                  endpoint: str,
                  params: dict = None
                  ):
        """
        BASE FUNCTION FOR MAKING API CALLS TO GRAVIEX
        """
        if not params:
            params = {}
        else:
            params = params

        path = _generate_path(params, endpoint)

        nonce = round(datetime.datetime.now().timestamp() * 1000000)

        key = base64.b64decode(self.api_secret)

        url = f'{BASEURL}{path}'
        print(path)
        request = Request(url)

        if method == POST:
            data = json.dumps({params}, separators=(',', ':'))
            message = str.encode(path + str(nonce) + data, "utf-8")
            request.data = str.encode(data, "utf-8")
            request.add_header(CONTENT_LENGTH, len(data))
        else:
            message = str.encode(path + str(nonce), "utf-8")

        hmacvar = hmac.new(key, message, sha512)

        signature = base64.b64encode(hmacvar.digest()).decode()

        request.method = method
        request.add_header(XAPIKEY, self.api_key)
        request.add_header(XAPINONCE, nonce)
        request.add_header(XAPISIGN, signature)

        self._wait()

        try:
            response = urlopen(request)
        except HTTPError as e:
            response = e
        return json.loads(bytes.decode(response.read()))

    def get_balance(self, currency):
        params = {CURRENCY: currency}
        return self._api_call(GET, BALANCE, params)

    def create_order(self, coin, side, amount, price, order_type=None):
        pair = _translate_coin_to_instrument(coin)
        params = {INSTRUMENT: pair, SIDE: side, VOLUME: amount}
        if order_type != STOPLIMIT:
            params.update({PRICE: price})
        if order_type is not None:
            params.update({TYPE: order_type})
        return self._api_call(POST, PLACEORDER, params)

    def get_all_coin_tickers(self):
        return self._api_call(GET, TICKERS)

    def get_order_book(self, coin, limit=25):
        pair = _translate_coin_to_instrument(coin)
        params = {INSTRUMENT: pair, LIMIT: limit}
        return self._api_call(GET, ORDERBOOK, params)
