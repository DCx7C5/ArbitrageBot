import collections
import hashlib
import hmac
import json
import base64

from requests import Session
import urllib.parse


class BaseClient:

    def __init__(self):
        self._api_key = None
        self._api_secret = None
        self._rate_limit = None
        self._last_call = None
        self.__pub_session = Session()
        self.__prv_session = Session()
        self.__headers = dict()
        self.__options = dict()

    def api_call(self, endpoint, params, api):
        return self.__fetch_wrap(path=endpoint, params=params, api=api)

    def sign_data_for_prv_api(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            pass

    def __fetch_wrap(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = self.sign_data_for_prv_api(path, api, method, params, headers, body)
        return self.__fetch(request['url'], request['method'], request['headers'], request['body'])

    def __request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        return self.__fetch_wrap(path, api, method, params, headers, body)

    def __prepare_request_headers(self, headers=None):
        headers = headers or {}
        headers.update(self.__headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def __fetch(self, url, method='GET', headers=None, body=None, api='public'):
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        if api != 'public':
            self.__prv_session.cookies.clear()
            response = self.__prv_session.request(method, url, data=body, headers=request_headers)
        else:
            self.__pub_session.cookies.clear()
            response = self.__pub_session.request(method, url, data=body, headers=request_headers)
        http_response = response.text
        json_response = json.loads(http_response)

        if json_response is not None:
            return json_response
        return http_response

    @staticmethod
    def _generate_path_from_params(params, endpoint):
        params_string = "?"
        for p in params:
            params_string += f'{p}={params[p]}' + "&"
        return f'{endpoint}{params_string[:-1]}'

    def __getitem__(self, item):
        return self.__getattribute__(item)
    
    @staticmethod
    def base64_url_encode(s):
        return base64.urlsafe_b64encode(s).decode().replace('=', '')

    @staticmethod
    def implode_params(string, params):
        if isinstance(params, dict):
            for key in params:
                if not isinstance(params[key], list):
                    string = string.replace('{' + key + '}', str(params[key]))
        return string

    @staticmethod
    def encode_uri_component(uri):
        return urllib.parse.quote(uri, safe="~()*!.'")

    @staticmethod
    def extend(*args):
        if args is not None:
            if type(args[0]) is collections.OrderedDict:
                result = collections.OrderedDict()
            else:
                result = {}
            for arg in args:
                result.update(arg)
            return result
        return {}

    @staticmethod
    def omit(d, *args):
        if isinstance(d, dict):
            result = d.copy()
            for arg in args:
                if type(arg) is list:
                    for key in arg:
                        if key in result:
                            del result[key]
                else:
                    if arg in result:
                        del result[arg]
            return result
        return d

    @staticmethod
    def url_encode(params=None):
        if params is None:
            params = {}
        if isinstance(params, dict) or isinstance(params, collections.OrderedDict):
            return urllib.parse.urlencode(params)
        return params

    @staticmethod
    def hmac(request, secret, algorithm=hashlib.sha256, digest='hex'):
        h = hmac.new(secret, request, algorithm)
        if digest == 'hex':
            return h.hexdigest()
        elif digest == 'base64':
            return base64.b64encode(h.digest())
        return h.digest()
