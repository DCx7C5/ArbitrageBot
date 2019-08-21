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

    def sign(self, path, api='public', method='GET', params=None, headers=None, body=None):
        pass

    def get_order_book(self, ref_id, limit=None):
        was_seen = set()
        bids = []
        asks = []
        params = {"market": ref_id,
                  'bids_limit': limit if limit else 100,
                  'asks_limit': limit if limit else 100}
        resp = self.api_call(ORDER_BOOK, params)
        print("dfg" + resp)
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

