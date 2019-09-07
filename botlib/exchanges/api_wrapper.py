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

    def get_order_book(self, exchange, ref_id, limit=None):
        """
        Function call to fetch order book from exchange

        """
        return self[exchange].get_order_book(ref_id, limit)

    def get_balance(self, exchange, refid=None):
        """
        Returns available Balance for refid

        """
        return self[exchange].get_available_balance(refid)

    # Function calls for order management:

    def create_limit_order(self, exchange, ref_id, side, price, volume):
        return self[exchange].create_order(ref_id, side, price, volume)

    def cancel_order(self, exchange, order_id):
        return self[exchange].cancel_order(order_id)

    def get_order_status(self, exchange, order_id):
        return self[exchange].get_order_status(order_id)

    # Function calls for client bot market settings:

    def withdrawal_is_allowed(self, exchange: str, refid: str) -> bool:
        """
        Checks if withdrawals are allowed for bot refid on exchange

        """
        if self[exchange].markets[refid]['withdrawal_allowed']:
            return True
        return False

    def deposit_is_allowed(self, exchange: str, refid: str) -> bool:
        """
        Checks if deposits are allowed for bot refid on exchange

        """
        if self[exchange].markets[refid]['deposit_allowed']:
            return True
        return False

    def get_min_profit_rate(self, exchange: str, refid: str):
        """
        Loads min_profit_rate from exchange dictionary (timer based updates)

        """
        return self[exchange].get_min_profit_rate(refid)

    def get_max_order_size_btc(self, exchange: str, refid: str):
        """
        Loads max_order_size from exchange dictionary (timer based updates)

        """
        return self[exchange].get_max_order_size_btc(refid)

    def get_minimum_order_amount(self, exchange: str, refid: str):
        """
        Returns minimum order amount of a market (timer based updates)

        """
        return self[exchange].get_min_order_vol(refid)

    def get_deposit_address(self, exchange: str, refid: str):
        """
        Returns deposit address for refid on exchange

        """
        return self[exchange].get_deposit_address(refid)

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)
