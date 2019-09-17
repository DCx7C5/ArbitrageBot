from threading import Lock

from botlib.storage import Storage


class MarketManager(Storage):
    """
    Market management and initialization class

    Attributes:
        all markets on exchange indexed with exchange specific refid
    """
    def __init__(self, api_data, sql_data):
        for market in api_data:
            refid = market['refid']
            self[refid] = Market(refid)
            self[refid].base_asset = market['base_asset']
            self[refid].quote_asset = market['quote_asset']
            self[refid].minimum_order_volume = float(market['minimum_order_volume'])
            self[refid].price_precision = int(market['price_precision'])
            self[refid].order_volume_precision = int(market['order_volume_precision'])
            self[refid].order_volume_step_size = float(market['order_volume_step_size'])
            self[refid].minimum_order_cost = float(market['minimum_order_cost']) if market['minimum_order_cost'] else 0.0000001

        for market in sql_data:
            self[market['refid']].minimum_profit_rate = float(market['min_profit'])
            self[market['refid']].maximum_order_cost = float(market['max_size'])
            self[market['refid']].deposit_address = market['deposit']


class Market(Storage):
    """Market helper class"""
    def __init__(self, refid: str):
        self.refid = refid
        self.__lock = Lock()
        self._base_asset = None
        self._quote_asset = None

        self._price_precision = None
        self._order_volume_step_size = None
        self._minimum_order_volume = None
        self._minimum_order_cost = None
        self._order_volume_precision = None

        # From Database
        self._minimum_profit_rate = 1
        self._maximum_order_cost = 0.00012

    @property
    def base_asset(self) -> str:
        with self.__lock:
            return self._base_asset

    @base_asset.setter
    def base_asset(self, value) -> None:
        with self.__lock:
            self._base_asset = value

    @property
    def quote_asset(self) -> str:
        with self.__lock:
            return self._quote_asset

    @quote_asset.setter
    def quote_asset(self, value) -> None:
        with self.__lock:
            self._quote_asset = value

    @property
    def price_precision(self) -> int:
        with self.__lock:
            return self._price_precision

    @price_precision.setter
    def price_precision(self, value) -> None:
        with self.__lock:
            self._price_precision = value

    @property
    def order_volume_step_size(self) -> float:
        with self.__lock:
            return self._order_volume_step_size

    @order_volume_step_size.setter
    def order_volume_step_size(self, value) -> None:
        with self.__lock:
            self._order_volume_step_size = value

    @property
    def minimum_order_volume(self) -> float:
        with self.__lock:
            return self._minimum_order_volume

    @minimum_order_volume.setter
    def minimum_order_volume(self, value) -> None:
        with self.__lock:
            self._minimum_order_volume = value

    @property
    def minimum_order_cost(self) -> float:
        with self.__lock:
            return self._minimum_order_cost

    @minimum_order_cost.setter
    def minimum_order_cost(self, value) -> None:
        with self.__lock:
            self._minimum_order_cost = value

    @property
    def minimum_profit_rate(self) -> float:
        with self.__lock:
            return self._minimum_profit_rate

    @minimum_profit_rate.setter
    def minimum_profit_rate(self, value) -> None:
        with self.__lock:
            self._minimum_profit_rate = value

    @property
    def maximum_order_cost(self) -> float:
        with self.__lock:
            return self._maximum_order_cost

    @maximum_order_cost.setter
    def maximum_order_cost(self, value) -> None:
        with self.__lock:
            self._maximum_order_cost = value

    @property
    def order_volume_precision(self) -> int:
        with self.__lock:
            return self._order_volume_precision

    @order_volume_precision.setter
    def order_volume_precision(self, value) -> None:
        with self.__lock:
            self._order_volume_precision = value

    def market_limits_to_dict(self) -> dict:
        """Creates dictionary from market all attributes"""
        with self.__lock:
            return {
                'minimum_order_volume': self._minimum_order_volume,
                'minimum_profit_rate': self._minimum_profit_rate,
                'minimum_order_cost': self._minimum_order_cost,
                'maximum_order_cost': self._maximum_order_cost,
                'price_precision': self._price_precision,
                'order_volume_precision': self._order_volume_precision,
                'order_volume_step_size': self._order_volume_step_size,
                'taker_fee': self._taker_fee,
                'maker_fee': self._maker_fee
            }

    def order_cost_limits_to_dict(self) -> dict:
        with self.__lock:
            return {
                'minimum_order_cost': self._minimum_order_cost,
                'maximum_order_cost': self._maximum_order_cost,
            }

    def order_volume_limits_to_dict(self) -> dict:
        with self.__lock:
            return {
                'minimum_order_volume': self._minimum_order_volume,
            }

    def precisions_and_step_sizes_to_dict(self) -> dict:
        with self.__lock:
            return {
                'price_precision': self._price_precision,
                'order_volume_precision': self._order_volume_precision,
                'order_volume_step_size': self._order_volume_step_size,
            }
