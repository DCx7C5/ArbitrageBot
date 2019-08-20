from botlib.exchanges.crex import CrexClient
from botlib.exchanges.graviex import GraviexClient
from botlib.sql.sql_functions import get_key_and_secret


class Exchange:

    def __init__(self):
        self.Crex24 = CrexClient(*get_key_and_secret('Crex24'))
        self.Graviex = GraviexClient(*get_key_and_secret('Graviex'))

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    def get_order_book(self, exchange, ref_id, limit=None):
        return self[exchange].get_order_book(ref_id, limit)

    def get_lowest_ask(self, exchange, ref_id):
        return self[exchange].get_lowest_ask(ref_id)

    def get_highest_bid(self, exchange, ref_id):
        return self[exchange].get_lowest_ask(ref_id)

    def get_balance(self, exchange, ref_id):
        return self[exchange].get_balance(ref_id)

    def create_buy_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def create_sell_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def cancel_order(self, exchange, order_id):
        return self[exchange].cancel_order(order_id)
