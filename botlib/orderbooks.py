from threading import RLock, Thread

from botlib.exchanges import Exchange
from botlib.storage import Storage


class OrderBooks(Storage):

    def __init__(self):
        self.__lock = RLock()

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

    def get_order_book(self, exchange, pair):
        try:
            with self.__lock:
                return self[exchange][pair]
        except (AttributeError, KeyError):
            raise Exception("OrderBook wasn't found in class OrderBooks(Storage)")
