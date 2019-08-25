import random
import time
from threading import Lock, Thread

from botlib.sql_functions import get_enabled_bots_ids_sql, get_enabled_bot_markets_sql
from botlib.storage import Storage


class BotsAndMarkets(Storage):
    """
    Storage class to store active Database values
    """
    def __init__(self, logger):
        self.__lock = Lock()
        self.__logger = logger

        # List of enabled bot ids
        self.__enabled_bot_ids = []

        # List with tuples (bot_id, exchange, refid) for FetchOrderBook
        self.__bot_markets = []

        # Dict with List  bot_id: [ (exch_0, book_0), (exch_1, book_1) ] for TradeOptionsFinder
        self.__markets_per_bot = {}

    def update_enabled_bot_ids(self, bot_ids: tuple or list):
        with self.__lock:
            for bot_id in bot_ids:
                if bot_id not in self.__enabled_bot_ids:
                    self.__enabled_bot_ids.append(bot_id)
                    self.__logger.info(f'Bot activated! Id: {bot_id}')

                if str(bot_id) not in self.__markets_per_bot.keys():
                    self.__markets_per_bot.update({str(bot_id): []})

        with self.__lock:
            for bot_id in self.__enabled_bot_ids:
                if bot_id not in bot_ids:
                    self.__enabled_bot_ids.remove(bot_id)
                    self.__logger.info(f'Bot deactivated! Id: {bot_id}')
                if str(bot_id) not in self.__markets_per_bot.keys():
                    del self.__markets_per_bot[str(bot_id)]

    def update_enabled_bot_markets(self, bot_markets: tuple or list):
        with self.__lock:
            for market in bot_markets:
                if market not in self.__bot_markets:
                    self.__bot_markets.append(market)
                    self.__markets_per_bot[str(market[0])].append((market[1], market[2]))
                    self.__logger.info(f'Market activated! Id: {market}')

            for market in self.__bot_markets:
                if market not in bot_markets:
                    self.__bot_markets.remove(market)
                    self.__markets_per_bot[str(market[0])].remove((market[1], market[2]))
                    self.__logger.info(f'Market deactivated! Id: {market}')

    def get_markets_per_bot(self) -> list:
        with self.__lock:
            return [(bot, self.__markets_per_bot[bot]) for bot in self.__markets_per_bot.keys() if len(self.__markets_per_bot[bot]) > 1]

    def get_bot_markets(self):
        with self.__lock:
            random.shuffle(list(self.__bot_markets))
            return self.__bot_markets

    def get_enabled_bot_ids(self):
        with self.__lock:
            return self.__enabled_bot_ids

    def count_enabled_bot_ids(self):
        with self.__lock:
            return len(self.__enabled_bot_ids)


class BotsAndMarketsDaemon(Thread):

    def __init__(self, bm_storage, logger):
        Thread.__init__(self)
        self.name = 'BackGroundSync'
        self.daemon = True
        self.__logger = logger
        self.__last_log_awake = 0
        self.__last_log_settings = 0
        self.__bm_storage = bm_storage

    def run(self):
        self.__logger.info('Daemon started!')
        while True:
            ids = get_enabled_bots_ids_sql()
            self.__bm_storage.update_enabled_bot_ids(ids)
            markets = get_enabled_bot_markets_sql(ids)
            self.__bm_storage.update_enabled_bot_markets(markets)
            time.sleep(1.5)
            if time.time() > self.__last_log_awake + 10:
                self.__logger.debug(f'Database syncing to bot....')
                self.__last_log_awake = time.time()
