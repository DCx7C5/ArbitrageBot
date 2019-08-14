from pprint import pprint

from botlib.exchanges.crex import CrexClient
from botlib.exchanges.graviex import GraviexClient
from botlib.sql.exchanges_sql import get_key_and_secret, get_exchanges_sql
from botlib.sql.sql_funcs import market_from_exchange


class Exchange:

    def __init__(self):
        self.crex = CrexClient(*get_key_and_secret('crex'))
        self.graviex = GraviexClient(*get_key_and_secret('graviex'))

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    def __iter__(self):
        return next(([self.graviex, self.crex]))

    def get_order_book(self, exchange, ref_id, limit=None):
        return self[exchange].get_order_book(ref_id, limit)

    def get_lowest_ask(self, exchange, ref_id):
        return self[exchange].get_lowest_ask(ref_id)

    def get_highest_bid(self, exchange, ref_id):
        return self[exchange].get_lowest_ask(ref_id)

    def get_balance(self, exchange, ref_id=None):
        return self[exchange].get_balance(ref_id)

    def get_fees(self, exchange, ref_id):
        return self[exchange].get_fees(ref_id)

    def create_buy_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def cancel_order(self, exchange, order_id):
        return self[exchange].cancel_order(order_id)

    def create_sell_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def update_prefs(self):
        pass

