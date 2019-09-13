from threading import Thread

from botlib.api_client.exchanges.binance import BinanceClient
from botlib.api_client.exchanges.crex import CrexClient
from botlib.api_client.exchanges.graviex import GraviexClient


class Exchange:
    """API client wrapper"""
    def __init__(self):
        self.Crex24 = CrexClient()
        self.Graviex = GraviexClient()
        self.Binance = BinanceClient()
        self.__extended_init()

    def get_order_book(self, exchange: str, ref_id: str, limit=None) -> tuple:
        """Function call to fetch order book from exchange"""
        return self[exchange].fetch_order_book(ref_id, limit)

    def get_balance(self, exchange: str, refid: str) -> float:
        """Returns available Balance for refid"""
        return self[exchange].get_balance(refid)

    # Function calls for order management:

    def create_limit_order(self, exchange, ref_id, price, volume, side):
        """Creates limit order"""
        return self[exchange].create_limit_order(ref_id, price, volume, side)

    def create_limit_buy_order(self, exchange, ref_id, price, volume):
        """Creates limit buy order"""
        return self[exchange].create_limit_order(ref_id, price, volume, side="buy")

    def create_limit_sell_order(self, exchange, ref_id, price, volume):
        """Creates limit sell order"""
        return self[exchange].create_limit_order(ref_id, price, volume, side="sell")

    def cancel_limit_order(self, exchange, order_id, refid=None):
        """Cancels order"""
        return self[exchange].cancel_limit_order(order_id, refid)

    def get_order_status(self, exchange, order_id, refid=None):
        """Returns order status"""
        return self[exchange].get_order_status(order_id, refid)

    # Function calls for client bot market settings:

    def withdrawal_is_allowed(self, exchange: str, refid: str) -> bool:
        """Checks if withdrawals are allowed for bot refid on exchange"""
        if self[exchange].markets[refid]['withdrawal_allowed']:
            return True
        return False

    def deposit_is_allowed(self, exchange: str, refid: str) -> bool:
        """Checks if deposits are allowed for bot refid on exchange"""
        if self[exchange].markets[refid]['deposit_allowed']:
            return True
        return False

    def get_min_profit_rate(self, exchange: str, refid: str):
        """Loads min_profit_rate from exchange dictionary (timer based updates)"""
        return self[exchange].get_min_profit_rate(refid)

    def get_max_order_size_btc(self, exchange: str, refid: str):
        """Loads max_order_size from exchange dictionary (timer based updates)"""
        return self[exchange].get_max_order_size_btc(refid)

    def get_minimum_order_amount(self, exchange: str, refid: str):
        """Returns minimum order amount of a market (timer based updates)"""
        return self[exchange].get_min_order_vol(refid)

    def get_deposit_address(self, exchange: str, refid: str):
        """Returns deposit address for refid on exchange"""
        return self[exchange].get_deposit_address(refid)

    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    def __extended_init(self):
        Thread(target=self.Crex24.update_balances).start()
        Thread(target=self.Graviex.update_balances).start()
        Thread(target=self.Binance.update_balances).start()
        Thread(target=self.Crex24.update_market_settings).start()
        Thread(target=self.Graviex.update_market_settings).start()
        Thread(target=self.Binance.update_market_settings).start()
