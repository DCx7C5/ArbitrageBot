import asyncio
import logging
import sys
from json import JSONDecodeError

from botlib.graviex import GraviexClientAIO, api_key, api_secret


class ArbitrageBot:

    def __init__(self):
        self.main_loop = asyncio.new_event_loop()
        self.active_exchanges = list()
        self.grav = GraviexClientAIO(api_key, api_secret)


    def start(self):
        self.main_loop.create_task(self.grav.get_sell_ticker('rvnbtc'))
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

