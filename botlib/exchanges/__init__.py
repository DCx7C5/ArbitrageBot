import time
from threading import Thread

from botlib.exchanges.binance import BinanceClient
from botlib.exchanges.crex import CrexClient
from botlib.exchanges.graviex import GraviexClient
from botlib.sql_functions import get_key_and_secret_sql


class Exchange:

    def __init__(self, logger=None):
        self.__logger = logger
        self.Crex24 = CrexClient(*get_key_and_secret_sql('Crex24'))
        self.Graviex = GraviexClient(*get_key_and_secret_sql('Graviex'))
        self.Binance = BinanceClient(*get_key_and_secret_sql('Binance'))
        self.__extended_inits__()

    def get_order_book(self, exchange, ref_id, limit=None):
        return self[exchange].get_order_book(ref_id, limit)

    def get_available_balance(self, exchange, refid=None):
        """Loads balance from exchange dictionary"""
        balance = self[exchange]['balances'].get(refid)
        if not balance:
            self[exchange].update_balance()
            return self[exchange]['balances'].get(refid)
        return balance

    def get_min_profit(self, exchange, refid):
        """Loads min_profit_rate from exchange dictionary"""
        min_profit = self[exchange]['min_profit'].get(refid)
        if (not min_profit) or time.time() > self[exchange].last_call_mp + 60:
            self[exchange].update_min_profit()
            self[exchange].last_call_mp = time.time()
            return self[exchange]['min_profit'].get(refid)
        return min_profit

    def get_max_order_size(self, exchange, refid):
        """Loads max_order_size from exchange dictionary"""
        max_size = self[exchange]['max_order_size'].get(refid)
        if (not max_size) or time.time() > self[exchange].last_call_ms + 60:
            self[exchange].update_max_order_size()
            self[exchange].last_call_mp = time.time()
            return self[exchange]['max_order_size'].get(refid)
        return max_size

    def get_minimum_order_amount(self, exchange, refid):
        """Returns minimum order amount of a market"""
        moa = self[exchange]['min_order_vol'].get(refid)
        if (not moa) or time.time() > self[exchange].last_call_moa + 3600:
            self[exchange].update_min_order_vol()
            self[exchange].last_call_moa = time.time()
            return self[exchange]['min_order_vol'][refid]
        return moa

    def create_buy_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def create_sell_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_buy_order(ref_id, price)

    def cancel_order(self, exchange, order_id):
        return self[exchange].cancel_order(order_id)

    def __extended_inits__(self):
        threads = [Thread(target=self.get_available_balance, args=("Crex24",)),
                   Thread(target=self.get_available_balance, args=("Binance",))]
        for t in threads:
            t.start()

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)
