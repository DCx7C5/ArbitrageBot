import random
import time
from threading import Lock, Thread
from collections import Counter

from botlib.sql_functions import get_enabled_bots_ids_sql, get_enabled_bot_markets_sql, disable_orphaned_bot_market_sql
from botlib.storage import Storage
from botlib.bot_log import daemon_logger

bad_logger = daemon_logger.getChild('BotMarkets')

bas_logger = bad_logger.getChild('Storage')


class BotsAndMarkets(Storage):
    """
    Storage class to store active Database values
    """
    def __init__(self):
        self.__lock = Lock()
        self.__logger = bas_logger

        # List of enabled bot ids
        self.__enabled_bot_ids = []

        # List with tuples (bot_id, exchange, refid) for FetchOrderBook
        self.__bot_markets = []

        # Dict with List  bot_id: [ (exch_0, book_0), (exch_1, book_1) ] for TradeOptionsFinder
        self.__markets_per_bot = {}

    def update_enabled_bot_ids(self, bot_ids: tuple or list) -> None:
        with self.__lock:
            for bot_id in bot_ids:
                if bot_id not in self.__enabled_bot_ids:
                    self.__enabled_bot_ids.append(bot_id)
                    self.__logger.warning(f'Bot activated! Id: {bot_id}')

                if str(bot_id) not in self.__markets_per_bot.keys():
                    self.__markets_per_bot.update({str(bot_id): []})

        with self.__lock:
            for bot_id in self.__enabled_bot_ids:
                if bot_id not in bot_ids:
                    self.__enabled_bot_ids.remove(bot_id)
                    self.__logger.warning(f'Bot deactivated! Id: {bot_id}')
                if str(bot_id) not in self.__markets_per_bot.keys():
                    del self.__markets_per_bot[str(bot_id)]

    def update_enabled_bot_markets(self, bot_markets: tuple or list) -> None:
        with self.__lock:
            for market in bot_markets:
                if market not in self.__bot_markets:
                    self.__bot_markets.append(market)
                    self.__markets_per_bot[str(market[0])].append((market[1], market[2]))
                    self.__logger.warning(f'Market activated! Id: {market}')

            for market in self.__bot_markets:
                if market not in bot_markets:
                    self.__bot_markets.remove(market)
                    self.__markets_per_bot[str(market[0])].remove((market[1], market[2]))
                    self.__logger.warning(f'Market deactivated! Id: {market}')
        orphan = self.find_orphan_markets()
        if orphan is not None and isinstance(orphan, tuple):
            self.__logger.error(f'Found orphaned bot_market: {orphan[1], orphan[2]} Deactivating now...')
            disable_orphaned_bot_market_sql(orphan[1])
            self.__logger.warning(f'There must be at least two bot_markets activated for each bot!')

    def find_orphan_markets(self):
        """This class checks for activated bots that have less than two bot_markets active"""
        with self.__lock:
            c = Counter(elem[0] for elem in self.__bot_markets)
            orphan = min(c, key=lambda x: c.get(x))
            if not orphan:
                return None
            if c[orphan] != 1:
                return None
            for i in self.__bot_markets:
                if i[0] == orphan:
                    return orphan, i[0], i[2]

    def get_markets_per_bot(self) -> list:
        with self.__lock:
            return [(bot, self.__markets_per_bot[bot]) for bot in self.__markets_per_bot.keys() if len(self.__markets_per_bot[bot]) > 1]

    def get_bot_markets(self) -> list:
        with self.__lock:
            random.shuffle(list(self.__bot_markets))
            return self.__bot_markets

    def get_enabled_bot_ids(self) -> list:
        with self.__lock:
            return self.__enabled_bot_ids

    def count_enabled_bot_ids(self) -> int:
        with self.__lock:
            return len(self.__enabled_bot_ids)


class BotsAndMarketsDaemon(Thread):

    def __init__(self, bm_storage):
        Thread.__init__(self)
        self.name = 'BackGroundSync'
        self.daemon = True
        self.__logger = bad_logger
        self.__last_log_awake = 0
        self.__last_log_settings = 0
        self.__bm_storage = bm_storage

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            ids = get_enabled_bots_ids_sql()
            self.__bm_storage.update_enabled_bot_ids(ids)
            markets = get_enabled_bot_markets_sql(ids)
            self.__bm_storage.update_enabled_bot_markets(markets)
            time.sleep(1)
            if time.time() > self.__last_log_awake + 15:
                self.__logger.info(f'Database syncing to bot....')
                self.__last_log_awake = time.time()
