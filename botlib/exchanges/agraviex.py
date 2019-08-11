import asyncio
import hmac
import time

import aiohttp
import hashlib
from aiohttp.client_exceptions import ContentTypeError

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


class GraviexClientAIO:

    def __init__(self, api_key, api_secret, loop=None, logger=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1 / 19.0
        self._last_call = None
        self._loop = loop or asyncio.get_event_loop()
        self._session = aiohttp.ClientSession()

    @staticmethod
    async def _initialize_session():
        return

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
                await asyncio.sleep(self.rate_limit - passed)
            self._last_call = self._loop.time()

    async def _api_call(self, method, endpoint, params, public=True):
        if not public:
            params.update({'tonce': int(self._loop.time() * 1000000), 'access_key': self.api_key})
            msg_string = await self._generate_message_string(method, endpoint, params)
            signature = await self._generate_hash_signature(msg_string)
            params.update({'signature': signature})
            await self._wait_async()
        url = f'{BASEURL}{endpoint}'
        async with self._session.request(method=method, url=url, params=params) as data:
            try:
                assert data.status == 200
                if await data.json() is None:
                    return data

                return await data.json()

            except AssertionError as e:
                # self._logger.error(e)
                pass
            except ContentTypeError as e:
                # self._logger.error(e)
                pass
            except RuntimeWarning as e:
                pass

    async def get_order_book(self, refid, asks_limit=None, bids_limit=None):
        params = {'market': refid}
        if asks_limit is not None:
            params.update({'asks_limit': asks_limit})
        if bids_limit is not None:
            params.update({'bids_limit': bids_limit})
        return await self._api_call(endpoint=ORDER_BOOK, method=GET, params=params)

    async def get_lowest_ask(self, refid, limit=10):
        data = await self.get_order_book(refid=refid, asks_limit=limit, bids_limit=limit)
        try:
            return data['asks'][0]['price']
        except Exception as e:
            print(e)
            pass

    async def get_highest_bid(self, refid, limit=10):
        data = await self.get_order_book(refid=refid, asks_limit=limit, bids_limit=limit)
        try:
            return data['bids'][0]['price']
        except Exception as e:
            print(e)
            pass

    async def close(self):
        await self._session.close()


async def test():
    grav = GraviexClientAIO('gx4D8JHsxTdXQGd2kdOVVxxc1GOTPC8YAK1Bbwa3', '7KNZMzxUNDcfSPxOJWJZMlW98VeeXaw0EcJPSHQP')
    while True:
        d = loop.call_soon_threadsafe(await grav.get_lowest_ask('dogebtc'))
        print(d)
        print(await grav.get_lowest_ask('dogebtc'))
        await asyncio.sleep(0.3)


loop = asyncio.get_event_loop()
loop.create_task(test())
loop.run_forever()