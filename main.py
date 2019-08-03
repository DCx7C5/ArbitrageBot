import sys
from json import JSONDecodeError

from botlib.graviex import GraviexClient, api_key, api_secret


class ArbitrageBot:

    def __init__(self):
        self.grav = GraviexClient(api_key, api_secret)

    def ticker_coroutine(self):
        while True:
            try:
                print(self.grav.get_ticker('rvnbtc').get('high'))
            except JSONDecodeError:
                pass


if __name__ == '__main__':
    bot = ArbitrageBot()
    try:
        bot.ticker_coroutine()
    except KeyboardInterrupt:
        sys.exit()