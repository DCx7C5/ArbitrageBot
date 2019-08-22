import time
import random
from queue import Queue
from threading import RLock, Thread, Lock
from botlib.sql_functions import get_enabled_bots_ids
from botlib.sql_functions import get_enabled_bot_markets_sql
from botlib.botlogs.logger import root_logger
from botlib.orderbooks import OrderBooks
from botlib.bot_locker import BotLocker
from botlib.exchanges import Exchange


class FetchOrderBook(Thread):

    def __init__(self, bot_id, exchange, refid):
        Thread.__init__(self)
        self.__bot_id = bot_id
        self._refid = refid
        self._exchange = exchange
        self.name = f"BotID {self.__bot_id} | {exchange} | {refid}"
        self._logger = root_logger

    def run(self):
        # Calls Exchange API
        data = ex.get_order_book(self._exchange, self._refid)
        if not data:
            self._logger.warning(f'API request failed with {self.__bot_id} | {self._exchange} | {self._refid}')

        # Stores OrderBook in OrderBook storage class
        success = ob.update_order_book(self._exchange, self._refid, data)
        if not success:
            self._logger.warning(f'Saving OrderBook failed with {self.__bot_id} | {self._exchange} | {self._refid}')
        if data and success:
            self._logger.debug("API call successful")


class OrderBookDaemon(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.name = 'OrderBookDaemon'
        self.__lock = RLock()
        self.__queue = Queue()
        self._logger = root_logger

    def fill_queue(self):
        if not bg_daemon.get_bot_markets():
            time.sleep(3)
        for bm in bg_daemon.get_bot_markets():
            self.__queue.put(bm)

    def run(self) -> None:
        self._logger.debug('Daemon started!')
        while True:
            if self.__queue.empty():
                self.fill_queue()
            args = self.__queue.get()
            t = FetchOrderBook(*args)
            t.start()
            time.sleep(0.2)


class BackGroundDaemon(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.name = 'BackGroundSync'
        self.daemon = True
        self.__lock = Lock()
        self._logger = root_logger

        # List of enabled bot ids
        self.enabled_bot_ids = []

        # List of locked bot ids
        self.locked_bot_ids = []

        # List with tuples (bot_id, exchange, refid)
        self.bot_markets = []

    def __update_enabled_bot_ids(self, bot_ids: tuple or list):
        for bid in bot_ids:
            if bid not in self.enabled_bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.append(bid)
                self._logger.info(f'Bot activated! Id: {bid} > Database has changed')
        for bid in self.enabled_bot_ids:
            if bid not in bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.remove(bid)
                self._logger.info(f'Bot deactivated! Id: {bid} > Database has changed')

    def remove_from_locked_bot_ids(self, bot_id: int):
        if not self.locked_bot_ids:
            return
        with self.__lock:
            self.locked_bot_ids.remove(bot_id)
        self._logger.debug(f'Bot released from execution lock: #{bot_id}')

    def add_to_locked_bot_ids(self, bot_id: int):
        with self.__lock:
            self.locked_bot_ids.append(bot_id)
        self._logger.debug(f'Bot added to block list. No work for him: #{bot_id}')

    def get_bot_markets(self):
        with self.__lock:
            random.shuffle(list(self.bot_markets))
            return self.bot_markets

    def count_enabled_bot_ids(self):
        with self.__lock:
            return len(self.enabled_bot_ids)

    def run(self):
        self._logger.info('Daemon started!')
        while True:
            ids = get_enabled_bots_ids()
            self.__update_enabled_bot_ids(ids)
            with self.__lock:
                self.bot_markets = get_enabled_bot_markets_sql(ids)
            time.sleep(1.5)


class TradeOptions(Thread):
    """
    Runs as daemon in background and loops through list of unique bot_ids
    to find arbitrage, catch_order, or any other trading opportunities .
    """

    def __init__(self):
        Thread.__init__(self)
        self.daemon = True
        self.name = f'TradeOptionDaemon'
        self._logger = root_logger

    def run(self) -> None:
        self._logger.info('Daemon started!')
        pass


ex = Exchange()
ob = OrderBooks()
bl = BotLocker()
bg_daemon = BackGroundDaemon()
obd = OrderBookDaemon()


if __name__ == '__main__':
    root_logger.info("Arbitrage Bot started")
    bg_daemon.start()
    obd.start()
    while True:
        root_logger.info('Main Thread is active!')
        time.sleep(10)

