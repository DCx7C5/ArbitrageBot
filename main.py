import concurrent.futures
import sys
import asyncio
import logging
import threading
import time
from pprint import pprint
from queue import Queue
from random import randint

from botlib.dbdaemon import BackgroundLogger
from botlib.sql.exchanges_sql import get_exchanges_sql
from botlib.sql.sql_funcs import get_actual_bot_markets, market_from_exchange
from botlib.sql.bot_markets_sql import get_bot_market_sql
from botlib.exchanges import Exchange


class CoinLock:

    def __init__(self):
        self._locked = []
        self._lock = threading.RLock()

    def add_to_locker(self, item):
        self._locked.append(item)

    def remove_from_locker(self, item):
        with self._lock:
            self._locked.remove(item)


class ArbitrageChecker(threading.Thread):

    def __init__(self, bot_id):
        super().__init__()
        self.bot_id = bot_id
        self.ex = ex
        self.name = f"Thread BotID {self.bot_id}"

    def compare_order_books(self, data: dict):
        """
        :param data: e.x. {crex: ((bids, vol), (asks, vol)}
        :rtype: str
        """
        # Get highest bid
        hb = max(data, key=lambda x: float(data.get(x)[0][0][0]))
        hbn = float(data.get(hb)[0][0][0])

        # Get lowest ask
        la = min(data, key=lambda x: float(data.get(x)[1][0][0]))
        lan = float(data.get(la)[0][0][0])

        # Check spread rate
        if round((hbn - lan) / hbn * hbn, 2) < 1:
            return False

        # Prevent other threads to start jobs with same bot_id
        c_lock.add_to_locker(self.bot_id)


    def


        return hbn, lan

    def fetch_order_books(self):
        obs = {}
        for mkt in get_actual_bot_markets(self.bot_id):
            obs.update({mkt[0]: self.ex.get_order_book(mkt[0], mkt[1])})
        la = self.compare_order_books(obs)
        pprint(la)

    def run(self) -> None:
        self._fetch_order_books()





if __name__ == '__main__':
    bgt = ArbitrageChecker(1)
    bgt.start()

    ex = Exchange()
    c_lock = CoinLock()

