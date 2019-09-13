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

    def get_order_rate_limits(self, exchange: str, refid: str):
        return self[exchange].get_order_rate_limits(refid)

    def get_order_volume_limits(self, exchange: str, refid: str):
        return self[exchange].get_order_volume_limits(refid)

    def get_order_price_limits(self, exchange: str, refid: str):
        return self[exchange].get_order_price_limits(refid)

    def get_order_cost_limits(self, exchange: str, refid: str):
        return self[exchange].get_order_cost_limits(refid)

    def get_transaction_limits(self, exchange: str, refid: str):
        return

    def get_crypto_deposit_address(self, exchange: str, refid: str):
        """Returns deposit address for refid on exchange"""
        return self[exchange].get_crypto_deposit_address(refid)

    def create_crypto_withdrawal(self, exchange: str, refid: str, amount: float):
        """Creates withdrawal of given asset and parameters"""
        return self[exchange].create_crypto_withdrawal(refid, amount)

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
