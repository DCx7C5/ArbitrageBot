import sys
import threading
from queue import Queue

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

    def main(self):
        pass


class ThreadPool:
    def __init__(self, num_t=5):
        self._q = Queue(num_t)
        # Create Worker Thread
        for _ in range(num_t):
            Worker(self._q)

    def add_task(self, f, *args, **kwargs):
        self._q.put((f, args, kwargs))

    def wait_complete(self):
        self._q.join()


if __name__ == '__main__':
    bot = ArbitrageBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        sys.exit()
