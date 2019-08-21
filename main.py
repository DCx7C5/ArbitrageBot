import random
import time
from pprint import pprint
from queue import Queue
from threading import RLock, Thread
from botlib.exchanges import Exchange
from botlib.sql.sql_functions import get_enabled_bots_ids, get_active_bot_markets_sql
from botlib.orderbooks import OrderBooks
from botlib.bot_locker import BotLocker


class FetchOrderBook(Thread):

    def __init__(self, bot_id, exchange, refid):
        Thread.__init__(self)
        self.__bot_id = bot_id
        self.name = f"BotID {self.__bot_id} | {exchange} | {refid}"
        self.__exchange = exchange
        self.__refid = refid

    def run(self):
        data = ex.get_order_book(self.__exchange, self.__refid)
        ob.update_order_book(self.__exchange, self.__refid, data)


class OrderBookDaemon(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.name = 'OrderBookDaemon'
        self.__lock = RLock()
        self.__queue = Queue()

    def fill_queue(self):
        if not bg_daemon.get_bot_markets():
            time.sleep(3)
        for bm in bg_daemon.get_bot_markets():
            self.__queue.put(bm)

    def run(self) -> None:
        while True:
            if self.__queue.empty():
                self.fill_queue()
            args = self.__queue.get()
            t = FetchOrderBook(*args)
            t.start()
            time.sleep(0.15)


class BackGroundDaemon(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.name = 'BackGroundSync'
        self.daemon = True
        self.__lock = RLock()

        # List of enabled bot ids
        self.enabled_bot_ids = []

        # List of locked bot ids
        self.locked_bot_ids = []

        # List with tuples (bot_id, exchange, refid)
        self.bot_markets = []

    def __update_enabled_bot_ids(self, bot_ids: list):
        for bid in bot_ids:
            if bid not in self.enabled_bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.append(bid)
                print(f"ADDED Bot ID {bid} TO self.__enabled_bot_ids")
        for bid in self.enabled_bot_ids:
            if bid not in bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.remove(bid)
                    self.remove_from_locked_bot_ids(bid)
                print(f"REMOVED Bot ID {bid} FROM self.__enabled_bot_ids")

    def remove_from_locked_bot_ids(self, bot_id: int):
        if not self.locked_bot_ids:
            return
        with self.__lock:
            self.locked_bot_ids.remove(bot_id)

    def add_to_locked_bot_ids(self, bot_id: int):
        with self.__lock:
            self.locked_bot_ids.append(bot_id)

    def get_bot_markets(self):
        with self.__lock:
            random.shuffle(self.bot_markets)
            return self.bot_markets

    def count_enabled_bot_ids(self):
        with self.__lock:
            return len(self.enabled_bot_ids)

    def run(self):
        while True:
            ids = get_enabled_bots_ids()
            self.__update_enabled_bot_ids(ids)
            with self.__lock:
                self.bot_markets = get_active_bot_markets_sql(ids)
            time.sleep(1.5)


class ArbitrageBot(Thread):

    def __init__(self):
        Thread.__init__(self)
        pass


class CatchOrderBot(Thread):

    def __init__(self, bot_id):
        super().__init__()
        self.bot_id = bot_id

        self.name = f"BotID {self.bot_id} | CatchOrder"


ex = Exchange()
ob = OrderBooks()
bl = BotLocker()
bg_daemon = BackGroundDaemon()
obd = OrderBookDaemon()


if __name__ == '__main__':
    bg_daemon.start()
    obd.start()
    while True:
        pprint(ob.__dict__)
        time.sleep(10)
