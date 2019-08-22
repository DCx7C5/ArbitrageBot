import collections
import contextlib
import hashlib
import hmac
import json
import base64
import warnings
from urllib import parse
from requests import Session
from urllib3.exceptions import InsecureRequestWarning

# SSL FIX
old_merge_environment_settings = Session.merge_environment_settings


class BaseClient:

    def __init__(self):
        self._pub_session = Session()
        self._prv_session = Session()
        self._headers = dict()
        self._options = dict()

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
        headers.update(self._headers)
        headers.update({'Accept-Encoding': 'gzip, deflate'})
        return headers

    def __fetch(self, url, method='GET', headers=None, body=None, api='public'):
        request_headers = self.__prepare_request_headers(headers)
        if body:
            body = body.encode()
        with no_ssl_verification():
            if api != 'public':
                self._prv_session.cookies.clear()
                response = self._prv_session.request(method=method, url=url, data=body,
                                                     headers=request_headers,
                                                     timeout=5)
            else:
                self._pub_session.cookies.clear()
                response = self._pub_session.request(method=method, url=url, data=body,
                                                     headers=request_headers,
                                                     timeout=5)
        http_response = response.text
        json_data = json.loads(http_response)

        if json_data is not None:
            return json_data
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
        return parse.quote(uri, safe="~()*!.'")

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
            return parse.urlencode(params)
        return params

    @staticmethod
    def hmac(request, secret, algorithm=hashlib.sha256, digest='hex'):
        h = hmac.new(secret, request, algorithm)
        if digest == 'hex':
            return h.hexdigest()
        elif digest == 'base64':
            return base64.b64encode(h.digest())
        return h.digest()


# noinspection PyBroadException
@contextlib.contextmanager
def no_ssl_verification():
    """
    Context wrapper function to catch and suppress SSL verification warnings
    with a simple 'with' clause. This class also changes the default value of
    requests.Session.verify_ssl and sets it to False
    e.x.:

    with no_ssl_verification():
        pass

    """
    opened_adapters = set()

    def merge_environment_settings(self, url, proxies, stream, verify, cert):
        opened_adapters.add(self.get_adapter(url))
        settings = old_merge_environment_settings(self, url, proxies, stream, verify, cert)
        settings['verify'] = False
        return settings
    Session.merge_environment_settings = merge_environment_settings
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', InsecureRequestWarning)
            yield
    finally:
        Session.merge_environment_settings = old_merge_environment_settings
        for adapter in opened_adapters:
            try:
                adapter.close()
            except:
                pass
