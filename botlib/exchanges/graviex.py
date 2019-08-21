import hmac
import json
import time
from hashlib import sha256
from requests import Session

from botlib.exchanges.baseclient import BaseClient


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
BALANCES = '/account/history'

# REQUEST METHODS
POST = "POST"
GET = "GET"


class GraviexClient(BaseClient):

    BASE_URL = 'https://graviex.net/api/v3'

    def __init__(self, api_key, api_secret, calls_per_second=15):
        BaseClient.__init__(self)
        self._api_key = api_key
        self._api_secret = api_secret
        self._rate_limit = 1.0 / calls_per_second

    def get_order_book(self, ref_id, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 100,
                  'asks_limit': limit if limit else 100}
        resp = self.api_call_public(path=ORDER_BOOK, params=params)
        # Volume addition of redundant positions
        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['bids']]:
            if p not in was_seen:
                was_seen.add(p)
                bids.append([p, v])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += v
        for p, v in [[float(x['price']), round(float(x['volume']), 10)] for x in resp['asks']]:
            if p not in was_seen:
                was_seen.add(p)
                asks.append([p, v])
            else:
                for t in bids:
                    if t[0] == p:
                        t[1] += v
        return bids, asks

    def get_balance(self, ref_id):
        currency = ref_id.lower()
        currency = currency.replace('btc', '') if ref_id != "btc" else None
        params = {"currency": currency}
        return self.__http_request(endpoint=BALANCES, method=GET, params=params, private=True)
