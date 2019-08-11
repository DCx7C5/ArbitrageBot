import asyncio
import time
import hmac
import aiohttp
import hashlib

BASEURL = 'https://graviex.net/api/v3'

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

# REQUEST METHODS
POST = "POST"
GET = "GET"

# API TYPE
PRIVATE = "PRIVATE"
PUBLIC = "PUBLIC"


class CrexClientAIO:

    def __init__(self, api_key, api_secret, loop=None, logger=None):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1 / 6.0
        self._last_call = None

    async def _generate_message_string(self, method, endpoint, params):
        params_str = ""
        for p in params:
            params_str += f"&{p}={params[p]}"
        return f'{method}|/api/v3{endpoint}|{params_str}'

    async def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()

    async def _api_call_public(self, method, endpoint, params):
        url = f'{BASEURL}{endpoint}'
        async with aiohttp.ClientSession() as session:
            if method is POST:
                data = await session.post(url, params=params)
            else:
                data = await session.get(url, params=params)
            try:
                assert data.status == 200
            except AssertionError as e:
                print(e)
            return await data.json()

    async def _api_call_private(self, method, endpoint, params):
        params.update({'tonce': int(time.time() * 1000), 'access_key': self.api_key})
        async with self._generate_message_string(method, endpoint, params) as msg_string:
            async with self._generate_hash_signature(msg_string) as signature:
                params.update({'signature': signature})
                url = f'{BASEURL}{endpoint}'
                async with aiohttp.ClientSession() as session:
                    await self._wait_async()
                    if method is POST:
                        data = await session.post(url, params=params)
                    else:
                        data = await session.get(url, params=params)
                    try:
                        assert data.status == 200
                    except AssertionError as e:
                        print(e)
                    return await data.json()

    async def get_order_book(self, refid, asks_limit=None, bids_limit=None):
        params = {'market': refid}
        if asks_limit is not None:
            params.update({'asks_limit': asks_limit})
        if bids_limit is not None:
            params.update({'bids_limit': bids_limit})
        return await self._api_call_public(endpoint=ORDER_BOOK, method=GET, params=params)

    async def get_lowest_ask(self, refid):
        data = await self.get_order_book(refid=refid, asks_limit=3, bids_limit=3)
        return data['asks'][0]['price']

    async def get_highest_bid(self, refid):
        data = await self.get_order_book(refid=refid, asks_limit=3, bids_limit=3)
        return data['bids'][0]['price']


if __name__ == '__main__':
    from pprint import pprint
    loop = asyncio.get_event_loop()
    grav = CrexClientAIO(
        'ea33efcd-71cc-4445-8ca5-61f85bb0d04b',
        '6SiG6QG2xmd8YD/+Jj8MfQysCldp8U7uS9CmZNIoTqY+cBXvMgbb6D108MtOuLabONpTBdb9rbhkBJ840srMvA=='
    )
    pprint("HighestBid " + loop.run_until_complete(grav.get_highest_bid('DOGE-BTC')))
    pprint("LowestAsk  " + loop.run_until_complete(grav.get_lowest_ask('DOGE-BTC')))
