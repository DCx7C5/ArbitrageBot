import asyncio
import time
import hmac
import httpx
import hashlib

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


class GraviexClientAIO:

    def __init__(self, api_key, api_secret, calls_per_second=15):
        self.api_key = api_key
        self.api_secret = api_secret
        self.rate_limit = 1.0 / calls_per_second
        self._last_call = None
        self.aio_client = httpx.AsyncClient()

    def _generate_request_string(self, params):
        params_string = ""
        for p in params:
            params_string += f'&{p}={params[p]}'
        return f'access_key={self.api_key}{params_string}&tonce={int(time.time() * 1000)}'

    def _generate_message_string(self, method, endpoint, params):
        return f'{method}|/api/v3{endpoint}|{self._generate_request_string(params=params)}'

    def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()

    async def _wait_async(self):
        if self._last_call is None:
            self._last_call = time.time()
        else:
            now = time.time()
            passed = now - self._last_call
            if passed < self.rate_limit:
                await asyncio.sleep(self.rate_limit - passed)
            self._last_call = time.time()

    async def _api_call_async(self, method: str,
                              endpoint: str,
                              params: dict = None,
                              spec_value=None):
        """
        BASE FUNCTION FOR MAKING ASYNC API CALLS TO GRAVIEX
        """
        if not params:
            params = {}
        else:
            params = params

        req_string = self._generate_request_string(params=params)

        msg_string = self._generate_message_string(method=method, endpoint=endpoint, params=params)

        signature = self._generate_hash_signature(msg_string)

        url = f'{BASEURL}{endpoint}?{req_string}&signature={signature}'

        params.update({'signature': signature})

        await self._wait_async()

        if method is POST:
            response = await self.aio_client.post(url, params=params)
        else:
            response = await self.aio_client.get(url, params=params)

        if spec_value is None:
            return response.json()

        return response.json()[spec_value]

    async def _list_orders_aio(self, **kwargs):
        params = {'market': 'all'}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return await self._api_call_async(endpoint=ORDERS, method=GET, params=params)

    async def _list_account_history_aio(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return await self._api_call_async(endpoint=ACCOUNT, method=GET, params=params)

    async def _generate_deposit_address_aio(self, coin):
        return await self._api_call_async(endpoint=GEN_DEPOSIT, method=GET, params={'currency': coin})

    async def _create_order_aio(self, **kwargs):
        params = {}
        for kw in kwargs:
            params.update({kw: kwargs[kw]})
        return await self._api_call_async(POST, ORDERS, params=params)

    async def _list_markets_aio(self, market_id=None):
        params = {}
        endpoint = MARKETS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return await self._api_call_async(endpoint=endpoint, method=GET, params=params)

    async def _list_tickers_aio(self, market_id=None, value=None):
        params = {}
        endpoint = TICKERS
        if market_id:
            endpoint += "/" + market_id
            params.update({'market': market_id})
        return await self._api_call_async(endpoint=endpoint, method=GET, params=params, spec_value=value)

    async def get_all_coin_tickers(self) -> dict:
        """
        Returns dictionary with all coin tickers
        """
        return await self._list_tickers_aio()

    async def get_ticker(self, coin) -> dict:
        """
        Returns a coin ticker
        """
        return await self._list_tickers_aio(coin)

    async def get_sell_ticker(self, coin):
        return print(await self._list_tickers_aio(coin, value='sell'))


