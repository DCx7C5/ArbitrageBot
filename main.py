import concurrent.futures
import sys
import asyncio
import logging
import threading
import time
from pprint import pprint
from queue import Queue
from random import randint

from botlib.sql.exchanges_sql import get_exchanges_sql
from botlib.sql.sql_funcs import bot_markets_from_bot_id, market_from_exchange
from botlib.sql.bot_markets_sql import get_bot_market_sql
from botlib.exchanges import Exchange



ex = Exchange()


class BackgroundLogger(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = "BackGroundDaemon"
        self._bm_lock = threading.RLock()
        self._quit_flag = False
        self._exchanges = False
        self._bot_markets = False



    def _db_calls(self):
        try:
            exs = get_exchanges_sql(active=True)
            if not exs:
                self._quit_flag = True
                self.daemon = False
            with self._bm_lock:
                self._exchanges = exs
            bms = get_bot_market_sql()
            if not bms:
                self._quit_flag = True
                self.daemon = False
            with self._bm_lock:
                self._bot_markets = bms
            time.sleep(randint(50, 100) / 10)
            return True
        except Exception as e:
            print(e)
            pass

    def quit(self):
        self._quit_flag = True
        del self



    def run(self) -> None:
        while not self._quit_flag:


class ArbitrageChecker(threading.Thread):

    def __init__(self, bot_id):
        super().__init__()
        self.bot_id = bot_id

        self.name = f"Thread BotID {self.bot_id}"
        self._hbe = None    # highest bid exchange
        self._lae = None    # lowest ask exchange

        self._hbn = None    # highest bid numeric
        self._lan = None    # lowest ask numeric

        self._hbv = None    # highest bid volume
        self._lav = None    # lowest ask volume
        self._data = None

    def arbitrage_check(self):

        # Get highest bid / volume
        self._hbe = max(self._data, key=lambda x: float(self._data.get(x)[0][0][0]))
        self._hbn = float(self._data.get(self._hbe)[0][0][0])

        # Get lowest ask / volume
        self._lae = min(self._data, key=lambda x: float(self._data.get(x)[1][0][0]))
        self._lan = float(self._data.get(self._lae)[1][0][0])

        # Check spread rate
        if round((self._hbn - self._lan) / self._hbn * self._hbn, 2) < 1:
            return False

        # Prevent other threads to start jobs with same bot_id
        c_lock.add_to_locker(self.bot_id)

        # Check Order Volume
        self._hbv = float(self._data.get(self._hbe)[0][0][1])
        self._lav = float(self._data.get(self._lae)[1][0][1])

        # Check that values not exceeding any limits (profit ra)
        if not (self.ex[self._hbe]['min_size'] > self._hbv < self.ex[self._hbe]['max_size']):
            return False
        if not (self.ex[self._lae]['min_size'] > self._lav < self.ex[self._lae]['max_size']):
            return False

        # Check against own coin balance (sell) and btc (buy)
        bal_c = self.ex[self._hbe]


        return True

    def fetch_order_books(self):
        self._data = {}
        for mkt in bot_markets_from_bot_id(self.bot_id):
            self._data.update({mkt[0]: self.ex.get_order_book(mkt[0], mkt[1])})
        self.arbitrage_check()
        return True

    def run(self) -> None:
        if self.fetch_order_books():
            pass
        if self.arbitrage_check():
            pass

        del self
        return


if __name__ == '__main__':

    c = CoinSettings()
    pprint(c.__dict__.get('prefs'))

