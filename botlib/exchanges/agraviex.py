import asyncio
import hmac
import aiohttp
import hashlib
from aiohttp.client_exceptions import ContentTypeError
from concurrent.futures import TimeoutError
BASEURL = 'https://graviex.net/api/v3'

# API ENDPOINTS
MARKETS = '/markets'
TICKERS = '/tickers'
ACCOUNT = '/account/history'
ORDERS = '/orders'
DEPOSIT_ADDR = '/deposit_address'
GEN_DEPOSIT = '/gen_deposit_address'
MEMBERS = '/members/me'
CANCEL = '/order/delete'
ORDER = '/order'
ORDER_BOOK = '/order_book'

# REQUEST METHODS
POST = "POST"
GET = "GET"

# API TYPE
PRIVATE = "PRIVATE"
PUBLIC = "PUBLIC"


settings = {
    'min_order_size_btc': 0.0005,
    'fees': None,
    }


class GraviexClientAIO:

    def __init__(self, api_key, api_secret, loop):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1 / 19.0
        self._last_call = None
        self._loop = loop if loop else asyncio.get_event_loop()
        self._session = aiohttp.ClientSession()

    @staticmethod
    async def _generate_message_string(method, endpoint, params):
        params_str = ""
        for p in params:
            params_str += f"&{p}={params[p]}"
        return f'{method}|/api/v3{endpoint}|{params_str}'

    async def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()

    async def _wait_async(self):
        if self._last_call is None:
            self._last_call = self._loop.time()
        else:
            now = self._loop.time()
            passed = now - self._last_call
            if passed < self.rate_limit:
                await self._loop.sleep(self.rate_limit - passed)
            self._last_call = self._loop.time()

    async def _api_call_public(self, method, endpoint, params):
        url = f'{BASEURL}{endpoint}'
        async with self._session.request(method=method, url=url, params=params) as request:
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

    async def _api_call_private(self, method, endpoint, params):
        params.update({'tonce': int(self._loop.time() * 1000000), 'access_key': self.api_key})
        msg_string = await self._generate_message_string(method, endpoint, params)
        signature = await self._generate_hash_signature(msg_string)
        params.update({'signature': signature})
        url = f'{BASEURL}{endpoint}'
        async with self._session.request(method=method, url=url, params=params) as data:
            try:
                assert data.status == 200
                if await data.json() is None:
                    return data
                return await data.json()
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

    async def get_order_book(self, ref_id, limit=None):
        params = {'market': ref_id}
        if limit is not None:
            params.update({'asks_limit': limit})
            params.update({'bids_limit': limit})

        return await self._api_call_public(endpoint=ORDER_BOOK, method=GET, params=params)

    async def get_lowest_ask(self, ref_id, limit=None):
        data = await self.get_order_book(ref_id=ref_id, limit=limit)
        try:
            return data['asks'][0]['price']
        except Exception as e:
            print(e)
            pass

    async def get_highest_bid(self, ref_id, limit=None):
        data = await self.get_order_book(ref_id=ref_id, limit=limit)
        try:
            return data['bids'][0]['price']
        except Exception as e:
            print(e)
            pass
