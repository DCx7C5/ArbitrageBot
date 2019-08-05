import datetime
import base64
import hmac
import json
import threading
import time
from hashlib import sha512
from urllib.request import urlopen, Request
from urllib.error import HTTPError

BASEURL = 'https://api.crex24.com'

# API ENDPOINTS
BALANCE = '/v2/account/balance'
PLACEORDER = "/v2/trading/placeOrder"

# REQUEST HEADER VARIABLES
XAPISIGN = 'X-CREX24-API-SIGN'
XAPIKEY = 'X-CREX24-API-KEY'
XAPINONCE = 'X-CREX24-API-NONCE'
CONTENT_LENGTH = "Content-Length"

# BALANCE PARAMETERS
CURRENCY = 'currency'

# ORDER PARAMETERS
INSTRUMENT = 'instrument'
SIDE = "side"
VOLUME = "volume"
PRICE = "price"
STOPPRICE = "stopPrice"
STRICTVALIDATION = "strictValidation"
TIMEINFORCE = "timeInForce"
TYPE = "type"
BUY = "buy"
SELL = "sell"

# ORDER TYPES
LIMIT = "limit"
MARKET = "market"
STOPLIMIT = "stopLimit"

# REQUEST TYPES
GET = 'GET'
POST = 'POST'


class CrexClient:

    def __init__(self, api_key, api_secret, calls_per_second=6):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None
        self._wait_lock = threading.RLock()

    def _generate_path(self, params, endpoint):
        params_string = ""
        for p in params:
            params_string += f'?{p}={params[p]}'
        return f'{endpoint}{params_string}'

    def _wait(self):
        with self._wait_lock:
            if self._last_call is None:
                self._last_call = time.time()
            else:
                now = time.time()
                passed = now - self._last_call
                if passed < self.rate_limit:
                    time.sleep(self.rate_limit - passed)
                self._last_call = time.time()

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

        path = self._generate_path(params, endpoint)

        nonce = round(datetime.datetime.now().timestamp() * 1000000)

        key = base64.b64decode(self.api_secret)

        url = f'{BASEURL}{path}'

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

    def create_order(self, pair, side, amount, price, order_type=None):
        params = {INSTRUMENT: pair, SIDE: side, VOLUME: amount}
        if order_type != STOPLIMIT:
            params.update({PRICE: price})
        if order_type is not None:
            params.update({TYPE: order_type})
        return self._api_call(POST, PLACEORDER, params)
