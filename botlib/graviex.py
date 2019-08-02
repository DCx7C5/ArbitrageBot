import time
import hmac
import hashlib

import requests

BASEURL = 'https://graviex.net/api/v3'

# API ENDPOINTS
MARKETS = '/markets'
TICKERS = '/tickers'

# REQUEST METHODS
PUT = "PUT"
DELETE = "DELETE"
POST = "POST"
GET = "GET"

api_key = "gx4D8JHsxTdXQGd2kdOVVxxc1GOTPC8YAK1Bbwa3"
api_secret = "7KNZMzxUNDcfSPxOJWJZMlW98VeeXaw0EcJPSHQP"


class GraviexClient:

    def __init__(self, api_key, api_secret):
        self.api_key = api_key
        self.api_secret = api_secret

    def _generate_hash_signature(self, msg_string):
        return hmac.new(key=self.api_secret.encode(),
                        msg=msg_string.encode(),
                        digestmod=hashlib.sha256).hexdigest()

    def _api_call(self, endpoint: str,
                  method: str,
                  params: dict = None):
        """
        BASE FUNCTION FOR MAKING API CALLS TO GRAVIEX
        """
        params_req_str = ""
        if not params:
            req_string = f'access_key={self.api_key}&tonce={int(time.time() * 1000)}'
        else:
            for i in params:
                params_req_str += f'&{i}={params[i]}'
            req_string = f'access_key={self.api_key}{params_req_str}&tonce={int(time.time() * 1000)}'

        if method is PUT:
            request = requests.put
        elif method is DELETE:
            request = requests.delete
        elif method is POST:
            request = requests.post
        elif method is GET:
            request = requests.get
        else:
            request = requests.get

        msg_string = f'{method}|/api/v3{endpoint}|{req_string}'

        signature = self._generate_hash_signature(msg_string)

        url = f'{BASEURL}{endpoint}?{req_string}&signature={signature}'

        response = request(url, params=params)

        assert response.status_code is 200

        return response.json()

    def _list_markets(self, market_id=None):
        if market_id is None:
            return self._api_call(endpoint=MARKETS, method=GET)
        return self._api_call(endpoint=MARKETS+"/"+market_id, method=GET, params={'market': market_id})

    def _list_tickers(self, market_id=None):
        if market_id is None:
            return self._api_call(endpoint=TICKERS, method=GET)
        return self._api_call(endpoint=TICKERS+"/"+market_id, method=GET, params={'market': market_id})

    def get_all_coin_tickers(self) -> dict:
        """
        Returns dictionary with all coin tickers
        """
        return self._list_tickers()

    def get_ticker(self, coin) -> dict:
        """
        Returns a coin ticker
        """
        return self._list_tickers(coin)

    def get_all_markets_by_name(self) -> list:
        """
        Returns a list of all available market pairs
        """
        return [m['name'] for m in self._list_markets()]

    def get_all_markets_by_id(self) -> list:
        """
        Returns a list of all available market pair ids
        """
        return [m['id'] for m in self._list_markets()]

    def get_market_info_by_id(self, market_id) -> dict:
        """
        Returns a dictionary with with market infos for specific pair
        """
        return self._list_markets(market_id)
