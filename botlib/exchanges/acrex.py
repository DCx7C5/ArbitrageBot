import asyncio
import base64
import concurrent
import hmac
import aiohttp
import hashlib

import yarl
from aiohttp import ContentTypeError
from concurrent.futures import TimeoutError

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


class CrexClientAIO:

    def __init__(self, api_key, api_secret, loop):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1 / 6.0
        self._last_call = None
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = aiohttp.ClientSession()

    async def _wait_async(self):
        if self._last_call is None:
            self._last_call = self._loop.time()
        else:
            now = self._loop.time()
            passed = now - self._last_call
            if passed < self.rate_limit:
                await self._loop.sleep(self.rate_limit - passed)
            self._last_call = self._loop.time()

    @staticmethod
    async def _generate_path(params, endpoint):
        params_string = "?"
        for p in params:
            params_string += f'{p}={params[p]}' + "&"
        return f'{endpoint}{params_string[:-1]}'

    async def _generate_hash_signature(self, msg_string):
        return hmac.new(key=base64.b64decode(self.api_secret),
                        msg=msg_string,
                        digestmod=hashlib.sha512).digest()

    async def _api_call_public(self, method: str, endpoint: str, params: dict):
        headers = {'Connection': 'keep-alive'}
        url = f'{BASE_URL}{endpoint}'
        async with self._session.request(method=method, url=yarl.URL(url), params=params, headers=headers) as request:
            try:
                assert request.status == 200
                if await request.json() is None:
                    return request
                return await request.json()
            except AssertionError as e:
                await asyncio.sleep(.001)
                pass
            except ContentTypeError as e:
                await asyncio.sleep(.001)
                pass
            except TimeoutError as e:
                await asyncio.sleep(.001)
                pass
            except RuntimeError as e:
                await asyncio.sleep(.001)
                pass

    async def _api_call_private(self, method: str, endpoint: str, params: dict):
        headers = {'Connection': 'keep-alive'}
        nonce = round(self._loop.time() * 1000000000)
        path = await self._generate_path(params, endpoint)
        msg_string = str.encode(path + str(nonce) + str(params), "utf-8")
        signature = await self._generate_hash_signature(msg_string)
        headers.update({X_API_KEY: self.api_key, X_API_NONCE: str(nonce), X_API_SIGN: signature})
        headers.update({CONTENT_LENGTH: len(params)})
        await self._wait_async()
        url = f'{BASE_URL}{endpoint}'
        async with self._session.request(method=method, url=yarl.URL(url), params=params, headers=headers) as request:
            try:
                assert request.status == 200
                if await request.json() is None:
                    return request
                return await request.json()
            except AssertionError as e:
                await asyncio.sleep(.001)
                pass
            except ContentTypeError as e:
                await asyncio.sleep(.001)
                pass

            except RuntimeError as e:
                await asyncio.sleep(.001)
                pass

    async def get_order_book(self, refid, limit=None):
        params = {'instrument': refid}
        if limit is not None:
            params.update({'limit': limit})
        return await self._api_call_public(endpoint=ORDER_BOOK, method=GET, params=params)

    async def get_lowest_ask(self, refid):
        data = await self.get_order_book(refid=refid, limit=100)
        return data['buyLevels'][0]['price']

    async def get_highest_bid(self, refid):
        data = await self.get_order_book(refid=refid, limit=100)
        return data['sellLevels'][0]['price']
