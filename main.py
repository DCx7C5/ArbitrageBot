import sys
import threading

from threading import RLock
from botlib.db_thread import DatabaseThread


class ArbitrageBot:

    def __init__(self):
        self.exchs = {}
        self.tickers = {}
        self.orderbook = {}
        self.coin_update_event = threading.Event()
        self.exch_update_event = threading.Event()

        self.threads = []

    def start(self):
        dbt = DatabaseThread(self.exch_update_event, self.coin_update_event)
        dbt.start()


if __name__ == '__main__':
    bot = ArbitrageBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit()
