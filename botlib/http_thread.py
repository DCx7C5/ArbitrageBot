from threading import Thread, Event, RLock

from botlib.db_thread import get_exchanges

ORDER_BOOK = {}
TICKERS = {}

ORDER_BOOK_LOCK = RLock()
TICKERS_LOCK = RLock()



class GetOrderBook(Thread):

    def __init__(self, thread_id: int or str, exchange, coin: str, event: Event, limit=None):
        Thread.__init__(self)
        self.name = f'GetOrderBook.{exchange.name.capitalize()}.{coin.upper()}.{thread_id}'
        self.coin = coin
        self.limit = limit
        self.exchange = exchange
        self.init_event = event

    def _get_order_book(self):
        with ORDER_BOOK_LOCK:
            func = self.exchange.get_order_book(self.coin, self.limit)
            ORDER_BOOK['buy'] = {self.exchange.name.lower(): func}
            ORDER_BOOK['sell'] = {self.exchange.name.lower(): func}

    def run(self) -> None:
        self._get_order_book()


class HttpThreads(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.exchanges = get_exchanges()

    def _update_tickers(self):

        func = self.exchanges[self.exchange].get_all_coin_tickers()
        with TICKERS_LOCK:
            for pair in func:
                if self.exchange == "graviex":
                    TICKERS.update({self.exchange: None})

    def run(self):
        while True:
            if self.e.is_set():
                self.exchange =
                self.init_event.clear()
                print("API ACTUALIZED")
            try:
                Thread(self._update_tickers('graviex')).start()
            except Exception:
                pass
