import time
from threading import Lock, Thread, enumerate

from botlib.botmarkets import BotsAndMarkets
from botlib.storage import Storage
from queue import Queue


class OrderBookTimer(Storage):

    def __init__(self):
        pass

    def update_timer(self, exchange, pair):
        t = time.time()
        if not self[exchange]:
            self[exchange] = {pair: t}

        elif not self[exchange].get(pair):
            self[exchange][pair] = t
        return True

    def check_bot_market_last_call(self, exchange, pair) -> bool:
        """Checks if job can be executed or scheduled"""
        try:
            if time.time() > (self[exchange].get(pair) + .9):
                self.update_timer(exchange, pair)
            return True
        except (KeyError, AttributeError, TypeError):
            self.update_timer(exchange, pair)


class OrderBook(Storage):

    def __init__(self):
        self.__lock = Lock()

    def update_order_book(self, exchange, pair, book):
        if not self[exchange]:
            with self.__lock:
                self[exchange] = {pair: book}
        elif not self[exchange].get(pair):
            with self.__lock:
                self[exchange].update({pair: book})
        else:
            with self.__lock:
                self[exchange][pair] = book
        return True

    def get_order_book(self, exchange, pair):
        try:
            with self.__lock:
                return self[exchange][pair]
        except (AttributeError, KeyError):
            time.sleep(2)
            self.get_order_book(exchange, pair)

    def get_highest_bid_position(self, exchange, pair):
        with self.__lock:
            return max(self[exchange][pair][0])

    def get_lowest_ask(self, exchange, pair):
        with self.__lock:
            return min(self[exchange][pair][1])


class FetchOrderBook(Thread):

    def __init__(self, bot_id, exchange, refid, clients, ob_storage: OrderBook, queue: Queue, logger):
        Thread.__init__(self)
        self.__bot_id = bot_id
        self._refid = refid
        self._exchange = exchange
        self._logger = logger
        self._clients = clients
        self._ob = ob_storage
        self.name = f"FetchOrderBook"
        self.queue = queue

    def run(self):
        # Calls Exchange API
        data = self._clients.get_order_book(self._exchange, self._refid)
        if not data:
            self._logger.error(f'API request failed with {self.__bot_id} | {self._exchange} | {self._refid}')

        # Stores OrderBook in OrderBook storage class
        success = self._ob.update_order_book(self._exchange, self._refid, data)
        if not success:
            self._logger.error(f'Saving OrderBook failed with {self.__bot_id} | {self._exchange} | {self._refid}')
        self.queue.task_done()


class OrderBookDaemon(Thread):

    def __init__(self, clients, bm_storage: BotsAndMarkets, ob_storage: OrderBook, logger):
        Thread.__init__(self)
        self.daemon = True
        self.name = 'OrderBookSync'
        self.queue = Queue()
        self._logger = logger
        self._clients = clients
        self._last_log = time.time()
        self._order_book = ob_storage
        self._bot_markets = bm_storage
        self._order_book_timer = OrderBookTimer()

    def __fill_queue(self):
        if not self._bot_markets.get_bot_markets():
            time.sleep(3)
        for bm in self._bot_markets.get_bot_markets():
            self.queue.put(bm)

    def run(self) -> None:
        self._logger.info('Daemon started!')
        while True:
            if self.queue.empty():
                self.__fill_queue()
            args = self.queue.get()
            if not self._order_book_timer.check_bot_market_last_call(args[1], args[2]):
                self.queue.task_done()
                continue
            else:
                FetchOrderBook(*args, self._clients,  self._order_book, self.queue, self._logger).start()
                if time.time() > self._last_log + 20:
                    self._logger.info(f'Exchanges syncing to bot... Sub-threads active:{self.__count_sub_threads()}')
                    self._last_log = time.time()
            time.sleep(0.25)

    @staticmethod
    def __count_sub_threads():
        return len([i for i in enumerate() if 'FetchOrderBook' in i.getName()])
