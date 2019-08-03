import asyncio
import sys
from json import JSONDecodeError

from botlib.graviex import GraviexClientAIO, api_key, api_secret


class ArbitrageBot:

    def __init__(self):
        self.main_loop = asyncio.get_event_loop()
        self.grav = GraviexClientAIO(api_key, api_secret)
        self.active_markets = {}

    async def ticker_coroutine(self):
        while True:
            try:
                ticker = await self.grav.get_ticker('rvnbtc')
                print(ticker.get('high'))
            except JSONDecodeError:
                pass

    def start(self):
        self.main_loop.create_task(self.ticker_coroutine())
        self.main_loop.run_forever()

    def quit(self):
        self.main_loop.close()


if __name__ == '__main__':
    bot = ArbitrageBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit()
        sys.exit()

