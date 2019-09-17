from threading import Thread

from botlib.api_client.exchanges.binance import BinanceClient
from botlib.api_client.exchanges.crex import CrexClient
from botlib.api_client.exchanges.graviex import GraviexClient
from botlib.bot_log import api_logger


class Exchange:
    """API client wrapper"""
    def __init__(self):
        self.Crex24 = CrexClient()
        self.Graviex = GraviexClient()
        self.Binance = BinanceClient()
        self.__extended_init()
        api_logger.debug("All exchanges initialized")

    def get_order_book(self, exchange: str, ref_id: str, limit=None):
        """
        Function call to fetch order book from exchange
        :returns:
            (
                bids,
                asks
            )
        """
        return self[exchange].fetch_order_book(
            refid=ref_id,
            limit=limit
        )

    def get_balance(self, exchange: str, refid: str) -> float:
        """
        Returns available Balance for refid
        :returns:
            0.0535432
        """
        return self[exchange].get_balance(refid)

    # Function calls for order management:

    def create_limit_order(self, exchange, ref_id, price, volume, side) -> dict:
        """
        Creates limit order
        :returns:
            {
                'refid': "dogebtc",
                'order_id': 3244844,
                'status': "done" or "",
                'side': "buy" or "sell"
                'price': 0.00003234,
                'volume': 102.00303.
                'executed_volume': 77.997,
                'created': datetime,
                'modified': datetime
            }
        """
        return self[exchange].create_limit_order(
            ref_id=ref_id,
            price=price,
            volume=volume,
            side=side
        )

    def create_limit_buy_order(self, exchange, ref_id, price, volume) -> dict:
        """
        Creates limit buy order
        :returns:
            {
                'refid': "dogebtc",
                'order_id': 3244844,
                'status': "done" or "",
                'side': "buy"
                'price': 0.00003234,
                'volume': 102.00303.
                'executed_volume': 77.997,
                'created': datetime,
                'modified': datetime
            }
        """
        return self[exchange].create_limit_order(
            ref_id=ref_id,
            price=price,
            volume=volume,
            side="buy"
        )

    def create_limit_sell_order(self, exchange, ref_id, price, volume) -> dict:
        """
        Creates limit sell order
        :returns:
            {
                'refid': "dogebtc",
                'order_id': 3244844,
                'status': "done" or "",
                'side': "sell"
                'price': 0.00003234,
                'volume': 102.00303.
                'executed_volume': 77.997,
                'created': datetime,
                'modified': datetime
            }
        """
        return self[exchange].create_limit_order(
            ref_id=ref_id,
            price=price,
            volume=volume,
            side="sell"
        )

    def cancel_limit_order(self, exchange, order_id, refid=None) -> bool:
        """
        Cancels order, returns True if request was successful
        :returns:
            True or False
        """
        return self[exchange].cancel_limit_order(
            order_id=order_id,
            refid=refid
        )

    def get_order_status(self, exchange, order_id, refid=None):
        """
        Returns order status
        :returns:
            {
                'refid': "dogebtc",
                'order_id': 3244844,
                'status': "done",
                'side': "sell" or "buy"
                'price': 0.00003234,
                'volume': 102.00303.
                'executed_volume': 102.00303,
                'created': datetime,
                'modified': datetime
            }
        """
        return self[exchange].get_order_status(
            order_id=order_id,
            refid=refid
        )

    def get_limits(self, exchange: str, refid: str) -> dict:
        """
        Get order and trading limits
        :returns:
            {
                'minimum_order_volume': 0.1,
                'minimum_order_cost': 0.000001,
                'maximum_order_cost': 0.00012
            }
        """
        return self[exchange].get_limits(refid=refid)

    def get_minimum_profit_rate(self, exchange: str, refid: str) -> float:
        """
        Calls rate limit dictionary from market manager class
        """
        return self[exchange].get_minimum_profit_rate(refid=refid)

    def get_crypto_deposit_address(self, exchange: str, refid: str) -> str:
        """
        Returns deposit address for refid on exchange
        :returns:
            dSDdadkADSLKASD0Ddfsdlkhsdhvuliu
        """
        return self[exchange].get_crypto_deposit_address(refid=refid)

    def create_crypto_withdrawal(self, exchange: str, refid: str, amount: float):
        """
        Creates withdrawal of given asset and parameters
        :returns:
            {
                'asset': "dogebtc",
                'withdrawal_id': 3244844,
                'status': ?,
                'send_to': "PJHemTQJZCpMKbXpbGvtRRxT9EEada8YUh"
                'fee': 0.00003234,
                'amount': 102.00303.
                'tx_id': 77.997,
                'created': datetime str,
                'processed': datetime str
            }
        """
        return self[exchange].create_crypto_withdrawal(
            refid=refid,
            amount=amount
        )

    def calculate_trading_fees(self, sell_market: dict, buy_market: dict):
        """
        Calculates and returns cost of trading fees
        :returns:

        """


    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    def __extended_init(self) -> None:
        """Thread based exchange initialization boost"""
        Thread(target=self.Crex24.update_balances).start()
        Thread(target=self.Graviex.update_balances).start()
        Thread(target=self.Binance.update_balances).start()
        Thread(target=self.Crex24.update_market_settings).start()
        Thread(target=self.Graviex.update_market_settings).start()
        Thread(target=self.Binance.update_market_settings).start()
