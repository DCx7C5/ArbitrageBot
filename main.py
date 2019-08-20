import threading
import time
from queue import Queue
from threading import RLock, Thread
from pprint import pprint
from botlib.exchanges import Exchange
from botlib.sql.sql_functions import get_enabled_bots_ids
from botlib.storage import Storage
from botlib.orderbooks import OrderBooks
from botlib.bot_locker import BotLocker
from botlib.bgsync import BackGroundDaemon

ex = Exchange()
ob = OrderBooks()
bl = BotLocker()
bg_daemon = BackGroundDaemon()
global_checkpoint = time.time()


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
            try:
                FetchOrderBook(*args).start()
            except:
                pass
            time.sleep(1)





class ArbitrageBot(Thread):

    def __init__(self):
        Thread.__init__(self)
        pass


class CatchOrderBot(Thread):

    def __init__(self, bot_id):
        super().__init__()
        self.bot_id = bot_id

        self.name = f"BotID {self.bot_id} | CatchOrder"


if __name__ == '__main__':
    obd = OrderBookDaemon()
    obd.start()
    while True:
        print(ob['Crex24'])
        time.sleep(2)