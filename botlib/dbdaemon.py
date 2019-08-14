import threading
import time
from random import randint


from botlib.sql.bot_markets_sql import get_bot_market_sql
from botlib.sql.exchanges_sql import get_exchanges_sql
from botlib.sql.sql_funcs import bot_markets_from_bot_id


class BotMarketSettings:

    def __init__(self):
        self._lock = threading.RLock()
        self._bot_markets = []
        self._bot_markets =


    def __getitem__(self, item):
        """Makes class subscribable"""
        return self.__getattribute__(item)

    def __setitem__(self, table, **kwargs):
        """Dictionary style storage management"""
        for kw in kwargs:
            self[table].update({kw: kwargs[kw]})





bg = BackgroundLogger()
bg.start()
