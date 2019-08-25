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
                    fmt='[%(asctime)-20s-] %(threadName)-16s - %(levelname)-6s >>> %(message)s',
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
        self.name = f'TradeOptionsFinder'
        self.cli = clients
        self.__logger = logger
        self.__bm_storage = bm_storage
        self.__ob_storage = ob_storage
        self.__jobs = []

    def find_arbitrage_options(self, bot):
        """Find arbitrage options for ALL market combinations (gets filtered later)"""
        options = []
        self.__logger.info(f"Bot Id:{bot[0]} is searching for arbitrage options...")
        order_books = self.__get_order_books_for_bot(bot)
        for bids in order_books:
            for asks in order_books:
                if bids is not asks :
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
        if round((bids[2][0] - asks[3][0]) / bids[2][0] * 100, 2) >= float(self.cli.get_min_profit(bids[0], bids[1])):
            return True
        return False

    def __check_quantity_against_min_order_amount(self, side):
        if self.cli.get_minimum_order_amount(side[0], side[1]) < side[2][1]:
            return True
        return False

    def __check_quantity_against_max_order_size(self, side):
        if self.cli.get_max_order_size(side[0], side[1]) > side[2][1]:
            return True
        return False

    def __filter_arbitrage_options(self, options):
        """
        Filters the found arbitrage options with some functions
        :param options: [(('Binance', 'ETHBTC', float(highest_bid), ('Crex', 'ETH-BTC', float(lowest_ask)), ...)
        """
        # First check the position quantity for exchange.min_order_qty < volume < database.max_size
        print(options)
        best_rate = 0
        best_option = None

        # First find most profitable option

    def __get_order_books_for_bot(self, bot) -> list:
        order_books = []
        for ob_rq in bot[1]:
            book = self.__ob_storage.get_order_book(ob_rq[0], ob_rq[1])
            order_books.append((ob_rq[0], ob_rq[1], book[0][0], book[1][0]))
        return order_books

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            for bot in self.__bm_storage.get_markets_per_bot():
                self.find_arbitrage_options(bot)
            time.sleep(1)


if __name__ == '__main__':
    exch_clients = Exchange()

    order_book_storage = OrderBook(
        logger=log
    )
    bots_markets_storage = BotsAndMarkets(
        logger=log
    )
    bots_markets_daemon = BotsAndMarketsDaemon(
        bm_storage=bots_markets_storage,
        logger=log
    )
    order_book_daemon = OrderBookDaemon(
        clients=exch_clients,
        logger=log,
        ob_storage=order_book_storage,
        bm_storage=bots_markets_storage
    )
    trade_finder = TradeOptionsDaemon(
        clients=exch_clients,
        bm_storage=bots_markets_storage,
        ob_storage=order_book_storage,
        logger=log
    )
    log.info("Arbitrage Bot started")
    bots_markets_daemon.start()
    order_book_daemon.start()
    time.sleep(15)
    trade_finder.start()
    trade_finder.join()
