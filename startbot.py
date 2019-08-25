import sys
import time
import logging
import coloredlogs
from threading import Thread
from botlib.exchanges import Exchange
from botlib.botmarkets import BotsAndMarkets, BotsAndMarketsDaemon
from botlib.orderbook import OrderBook, OrderBookDaemon

log = logging.getLogger(__name__)
fh = logging.FileHandler('botlib/botlogs/debug.log')
coloredlogs.install(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='[%(asctime)-20s-] %(threadName)-14s - %(levelname)-7s > %(message)s',
                    milliseconds=True,
                    logger=log
                    )


class TradeOptionsDaemon(Thread):
    """
    Runs as daemon in background and loops through list of unique bot_ids
    to find arbitrage, catch_order, or any other trading opportunities .
    """

    def __init__(self, clients: Exchange, bm_storage: BotsAndMarkets, ob_storage: OrderBook, logger):
        Thread.__init__(self)
        self.daemon = True
        self.name = f'TradeFinder'
        self.__cli = clients
        self.__logger = logger
        self.__last_log = time.time()
        self.__bm_storage = bm_storage
        self.__ob_storage = ob_storage
        self.__active_bots = list()
        self.__jobs = list()
        self.__ec = 0

    def find_arbitrage_options(self, bot):
        """Find arbitrage options for ALL market combinations"""
        options = []
        order_books = self.__get_order_books_for_bot(bot)
        if not order_books or order_books is None:
            self.__logger.warning(order_books)
        for bids in order_books:
            for asks in order_books:
                if bids is not asks:
                    if not self.__check_min_profit(bids, asks):
                        continue
                    if not self.__check_quantity_against_min_order_amount(bids):
                        continue
                    if not self.__check_quantity_against_max_order_size(bids):
                        continue
                    options.append(((bids[0], bids[1], bids[2][0], bids[2][1]), (asks[0], asks[1], asks[3][0], asks[3][1])))
        if options:
            self.__filter_arbitrage_options(options)

    def __check_min_profit(self, bids, asks):
        if round((bids[2][0] - asks[3][0]) / bids[2][0] * 100, 2) >= float(self.__cli.get_min_profit(bids[0], bids[1])):
            return True
        return False

    def __check_quantity_against_min_order_amount(self, side):
        if self.__cli.get_minimum_order_amount(side[0], side[1]) < side[2][1]:
            return True
        return False

    def __check_quantity_against_max_order_size(self, side):
        if self.__cli.get_max_order_size(side[0], side[1]) > side[2][1]:
            return True
        return False

    def __filter_arbitrage_options(self, options):
        """
        Filters the found arbitrage options
        """
        print(options)
        best_rate = 0
        best_option = None

        # First find most profitable option

    def __get_order_books_for_bot(self, bot) -> list:
        order_books = []
        for ob_rq in bot[1]:
            try:
                book = self.__ob_storage.get_order_book(ob_rq[0], ob_rq[1])
                order_books.append((ob_rq[0], ob_rq[1], book[0][0], book[1][0]))
            except TypeError:
                time.sleep(3)
                self.__logger.warning('Markets not synced yet...')
                self.__get_order_books_for_bot(bot)
        return order_books

    def __update_active_bots(self):
        bots = self.__bm_storage.get_enabled_bot_ids()
        for bot_id in bots:
            if bot_id not in self.__active_bots:
                self.__active_bots.append(bot_id)
        for bot_id in self.__active_bots:
            if bot_id not in bots:
                self.__active_bots.remove(bot_id)

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            bots_mpb = self.__bm_storage.get_markets_per_bot()
            if bots_mpb:
                for bot in bots_mpb:
                    self.find_arbitrage_options(bot)
            else:
                self.__logger.warning('Markets not synced yet...')
            self.__update_active_bots()
            if time.time() > self.__last_log + 10:
                self.__logger.debug(f"Bots {self.__active_bots} are searching for arbitrage options...")
                self.__last_log = time.time()
            time.sleep(1)


if __name__ == '__main__':
    # Initialize exchange APIs
    exch_clients = Exchange(logger=log)

    # Create order book storage
    order_book_storage = OrderBook(logger=log)

    # Create bots_markets storage
    bots_markets_storage = BotsAndMarkets(logger=log)

    # Init database sync daemon
    bots_markets_daemon = BotsAndMarketsDaemon(
        bm_storage=bots_markets_storage,
        logger=log)

    # Init order_book daemon
    order_book_daemon = OrderBookDaemon(
        clients=exch_clients,
        logger=log,
        ob_storage=order_book_storage,
        bm_storage=bots_markets_storage)

    # Init trade-finder daemon (arbitrage, catch, etc..)
    trade_finder = TradeOptionsDaemon(
        clients=exch_clients,
        bm_storage=bots_markets_storage,
        ob_storage=order_book_storage,
        logger=log)

    log.info("Arbitrage Bot initialized. Starting bot!")

    # Let the daemons run in background
    try:
        bots_markets_daemon.start()
        order_book_daemon.start()
        time.sleep(5)
        trade_finder.start()
        trade_finder.join()
    except KeyboardInterrupt:
        log.info('Shutdown By User')
    finally:
        sys.exit()
