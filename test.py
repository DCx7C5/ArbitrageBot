import datetime
import base64
import hmac
from hashlib import sha512
from urllib.request import urlopen, Request
from urllib.error import HTTPError

baseUrl = "https://api.crex24.com"
apiKey = "ea33efcd-71cc-4445-8ca5-61f85bb0d04b"
secret = "6SiG6QG2xmd8YD/+Jj8MfQysCldp8U7uS9CmZNIoTqY+cBXvMgbb6D108MtOuLabONpTBdb9rbhkBJ840srMvA=="

path = "/v2/account/balance?currency=BTC"
nonce = round(datetime.datetime.now().timestamp() * 1000000)
print(nonce)
key = base64.b64decode(secret)
message = str.encode(path + str(nonce), "utf-8")
hmacv = hmac.new(key, message, sha512)
signature = base64.b64encode(hmacv.digest()).decode()
print(baseUrl + path)
request = Request(baseUrl + path)
request.method = "GET"
request.add_header("X-CREX24-API-KEY", apiKey)
request.add_header("X-CREX24-API-NONCE", nonce)
request.add_header("X-CREX24-API-SIGN", signature)

try:
    response = urlopen(request)
except HTTPError as e:
    response = e

status = response.getcode()
body = bytes.decode(response.read())

print("Status code: " + str(status))
print(body)