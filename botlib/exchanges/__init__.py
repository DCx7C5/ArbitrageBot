from threading import Thread
from botlib.exchanges.binance import BinanceClient
from botlib.exchanges.crex import CrexClient
from botlib.exchanges.graviex import GraviexClient
from botlib.sql_functions import get_key_and_secret_sql


class Exchange:
    """API client wrapper"""
    def __init__(self):
        self.Crex24 = CrexClient(*get_key_and_secret_sql('Crex24'))
        self.Graviex = GraviexClient(*get_key_and_secret_sql('Graviex'))
        self.Binance = BinanceClient(*get_key_and_secret_sql('Binance'))
        self.__extended_inits__()

    def get_order_book(self, exchange, ref_id, limit=None):
        return self[exchange].get_order_book(ref_id, limit)

    def get_balance(self, exchange, refid=None):
        """Returns available Balance for refid"""
        return self[exchange].get_available_balance(refid)

    def get_min_profit(self, exchange, refid):
        """Loads min_profit_rate from exchange dictionary (timer based updates)"""
        return self[exchange].get_min_profit(refid)

    def get_max_order_size(self, exchange, refid):
        """Loads max_order_size from exchange dictionary (timer based updates)"""
        return self[exchange].get_max_order_size(refid)

    def get_minimum_order_amount(self, exchange, refid):
        """Returns minimum order amount of a market (timer based updates)"""
        return self[exchange].get_min_order_vol(refid)

    def get_deposit_address(self, exchange, refid):
        """Returns deposit address for refid on exchange"""
        return self[exchange].get_deposit_address(refid)

    def create_sell_order(self, exchange, ref_id, price, volume):
        return self[exchange].create_sell_order(ref_id, price, volume)

    def create_buy_order(self, exchange, ref_id, price, volume):
        """"""
        return self[exchange].create_buy_order(ref_id, price, volume)

    def cancel_order(self, exchange, order_id):
        return self[exchange].cancel_order(order_id)

    def check_order(self, exchange, order_id):
        return self[exchange].check_order(order_id)

    def __extended_inits__(self):
        last_t = None
        threads = [
            Thread(target=self.get_balance, name='ClientSettings', args=("Crex24",)),
            Thread(target=self.get_balance, name='ClientSettings', args=("Binance",)),
            Thread(target=self.get_balance, name='ClientSettings', args=("Graviex",)),
        ]
        for t in threads:
            t.start()
            last_t = t
        last_t.join()

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)
