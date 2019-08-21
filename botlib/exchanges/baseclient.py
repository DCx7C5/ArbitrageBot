import collections
import gzip
import hashlib
import hmac
import io
import json
import re
import ssl
import base64
import time
import zlib

from requests import Session
import urllib.parse as _url_encode


ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


class BaseClient:

    BASE_URL_V1 = None

    def __init__(self):
        self._api_key = None
        self._api_secret = None
        self._rate_limit = None
        self._last_call = None
        self.session = Session()
        self.headers = dict()
        self.options = dict()

    def api_call(self, endpoint, params, api):
        return self.__fetch2(path=endpoint, params=params, api=api)

    def sign(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        raise Exception('sign() pure method must be redefined in derived classes')

    def __fetch2(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        request = self.sign(path, api, method, params, headers, body)
        return self.fetch(request['url'], request['method'], request['headers'], request['body'])

    def __request(self, path, api='public', method='GET', params=None, headers=None, body=None):
        if params is None:
            params = {}
        return self.__fetch2(path, api, method, params, headers, body)

    def parse_json(self, http_response):
        if BaseClient.is_json_encoded_object(http_response):
            return json.loads(http_response)

    def __prepare_request_headers(self, headers=None):
        headers = headers or {}
        headers.update(self.headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def fetch(self, url, method='GET', headers=None, body=None):
        """Perform a HTTP request and return decoded JSON data"""
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        self.session.cookies.clear()
        response = self.session.request(method, url, data=body, headers=request_headers)
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
        """Makes class subscribable"""
        return self.__getattribute__(item)
    
    @staticmethod
    def base64_url_encode(s):
        return BaseClient.decode(base64.urlsafe_b64encode(s)).replace('=', '')

    @staticmethod
    def is_json_encoded_object(input):
        return (isinstance(input, str) and
                (len(input) >= 2) and
                ((input[0] == '{') or (input[0] == '[')))

    @staticmethod
    def decode(string):
        return string.decode()

    @staticmethod
    def gzip_deflate(response, text):
        encoding = response.info().get('Content-Encoding')
        if encoding in ('gzip', 'x-gzip', 'deflate'):
            if encoding == 'deflate':
                return zlib.decompress(text, -zlib.MAX_WBITS)
            else:
                return gzip.GzipFile('', 'rb', 9, io.BytesIO(text)).read()
        return text

    @staticmethod
    def extract_params(string):
        return re.findall(r'{([\w-]+)}', string)

    @staticmethod
    def implode_params(string, params):
        if isinstance(params, dict):
            for key in params:
                if not isinstance(params[key], list):
                    string = string.replace('{' + key + '}', str(params[key]))
        return string

    @staticmethod
    def encode_uri_component(uri):
        return _url_encode.quote(uri, safe="~()*!.'")

    @staticmethod
    def extend(*args):
        if args is not None:
            result = None
            if type(args[0]) is collections.OrderedDict:
                result = collections.OrderedDict()
            else:
                result = {}
            for arg in args:
                result.update(arg)
            return result
        return {}

    @staticmethod
    def unjson(input):
        return json.loads(input)

    @staticmethod
    def json(data, params=None):
        return json.dumps(data, separators=(',', ':'))

    @staticmethod
    def encode(string):
        return string.encode()

    def nonce(self):
        return time.time()

    @staticmethod
    def url(path, params=None):
        if params is None:
            params = {}
        result = BaseClient.implode_params(path, params)
        query = BaseClient.omit(params, BaseClient.extract_params(path))
        if query:
            result += '?' + _url_encode.urlencode(query)
        return result

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
        if (type(params) is dict) or isinstance(params, collections.OrderedDict):
            return _url_encode.urlencode(params)
        return params

    @staticmethod
    def raw_encode(params=None):
        if params is None:
            params = {}
        return _url_encode.unquote(BaseClient.url_encode(params))

    @staticmethod
    def hmac(request, secret, algorithm=hashlib.sha256, digest='hex'):
        h = hmac.new(secret, request, algorithm)
        if digest == 'hex':
            return h.hexdigest()
        elif digest == 'base64':
            return base64.b64encode(h.digest())
        return h.digest()
