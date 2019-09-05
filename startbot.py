import sys
import time
from random import randint
from threading import Thread
from botlib.exchanges import Exchange
from botlib.bot_log import daemon_logger
from botlib.blocked_markets import BlockedMarkets
from botlib.order_book import OrderBook, OrderBookDaemon
from botlib.bot_markets import BotsAndMarkets, BotsAndMarketsDaemon


class TradeOptionsDaemon(Thread):
    """
    Runs as daemon in background and loops through list of unique bot_ids
    to find arbitrage, catch_order, or any other trading opportunities .
    """

    def __init__(self, clients: Exchange, bm_storage: BotsAndMarkets, ob_storage: OrderBook, blocked_markets: BlockedMarkets):
        Thread.__init__(self)
        self.daemon = True
        self.name = f'TradeOptions'
        self.__cli = clients
        self.__logger = daemon_logger.getChild('Arbitrage')
        self.__last_log = time.time()
        self.__bm_storage = bm_storage
        self.__ob_storage = ob_storage
        self.__market_locker = blocked_markets
        self.__active_bots = []
        self.__ec = 0
        self.__last_run = time.time()

    def __find_arbitrage_options(self, bot):
        """Find arbitrage options for ALL market combinations then filters"""
        options = []
        order_books = self.__get_order_books_for_bot(bot)
        if not order_books or order_books is None:
            self.__logger.warning(order_books)
        # Create options with checking min profit rate
        for bids in order_books:
            for asks in order_books:
                if bids is not asks:
                    if self.__check_min_profit(bids, asks):
                        options += [
                            [
                                [bids[0], bids[1], bids[2][0], bids[2][1]],
                                [asks[0], asks[1], asks[3][0], asks[3][1]]
                            ]
                        ]

        # More filters on arbitrage options
        if options:
            self.__filter_arbitrage_options(options)

    def __check_min_profit(self, bids, asks):
        rate = round((bids[2][0] - asks[3][0]) / bids[2][0] * 100, 2)
        if rate >= float(self.__cli.get_min_profit(bids[0], bids[1])):
            return True
        return False

    def __filter_arbitrage_options(self, options):
        """
        Filters the found arbitrage options
        """
        # Check against min order amount on exchange
        options = self.__check_quantity_against_min_order_amount(options)

        # Define max amount on exchange
        options = self.__define_max_order_size_per_option(options)

        # Check balances for each option
        options = self.__check_balances_per_option(options)

        # Calculate profit per option
        options = self.__calculate_profit_per_option(options)

        # Find most profitable option, set as job, and lock job markets
        job = self.__filter_based_on_most_profitable(options)
        self.__logger.warning(f'Job found! {job}')

    def __check_quantity_against_min_order_amount(self, options: list) -> list:
        """
        First filter on arbitrage options
            -removes arbitrage option, if
        """
        for opt in options:
            for side in opt:
                if not float(self.__cli.get_minimum_order_amount(side[0], side[1])) < side[3]:
                    options.remove(opt)
        return options

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

    def __define_max_order_size_per_option(self, options):
        """
        Second Filter on arbitrage options
            -defines the amount of coins to buy, based on max order size
        """
        for opt in options:
            for side in opt:
                max_order_size = float(self.__cli.get_max_order_size(side[0], side[1]))
                if (side[2] * side[3]) < max_order_size:
                    order_size_max = round(side[3], 8)
                else:
                    order_size_max = round(max_order_size / side[2], 8)
                side.append(order_size_max)
            possible = min(opt[0][4], opt[1][4])
            opt[0][4] = possible
            opt[1][4] = possible
        return options

    def __check_balances_per_option(self, options):
        """
        Third filter on arbitrage options
            - checks sell-market and buy-market balances
        """
        for opts in options:

            # Check balance sell_market
            sell_amount = opts[0][-1]
            balance_coin = float(self.__cli.get_balance(opts[0][0], opts[0][1]))
            if balance_coin < sell_amount:
                opts[0][-1] = balance_coin
                opts[1][-1] = balance_coin

            # Check balance btc on buy market
            buy_amount = opts[1][-1]
            buy_price = opts[1][2]
            buy_amount_in_btc = round(buy_amount * buy_price, 8)
            balance_btc = float(self.__cli.get_balance(opts[1][0], 'BTC'))

            if balance_btc < buy_amount_in_btc:
                opts[0][-1] = round(float(balance_btc / buy_price), 8)
                opts[1][-1] = round(float(balance_btc / buy_price), 8)

        return options

    @staticmethod
    def __calculate_profit_per_option(options):
        """
        Fourth filter on arbitrage options
            - calculates most profitable arbitrage option
        """
        for opt in options:
            sell_market = opt[0][4] * opt[0][2]
            buy_market = opt[1][4] * opt[1][2]
            profit = round(float(sell_market - buy_market), 8)
            opt.append(profit)
        return options

    def __filter_based_on_most_profitable(self, options):
        _opt = None
        _val = 0
        for opts in options:
            if opts[-1] > _val:
                _opt = opts
                _val = opts[-1]
        self.__market_locker.add_to_blocked_list(_opt[0][0], _opt[0][1])
        self.__market_locker.add_to_blocked_list(_opt[1][0], _opt[1][1])
        return _opt

    def __update_active_bots(self):
        bots = self.__bm_storage.get_enabled_bot_ids()
        for bot_id in bots:
            if bot_id not in self.__active_bots:
                self.__active_bots.append(bot_id)
        for bot_id in self.__active_bots:
            if bot_id not in bots:
                self.__active_bots.remove(bot_id)

    def __exclude_blocked_markets(self, bots_mpb):
        """If exchange + market is locked it gets removed from bots bot-market-list"""
        for i in bots_mpb:
            for x in i[1]:
                if x in self.__market_locker.get_blocked_list():
                    i[1].remove(x)
        return bots_mpb

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            # Get list with bots and their bot_markets
            bots_mpb = self.__bm_storage.get_markets_per_bot()

            # Check if items are in bots_mpb
            if bots_mpb:
                # Remove bot markets from bot, that are in block-list (processed in a job right now)
                excl_bots_mpb = self.__exclude_blocked_markets(bots_mpb)
                for bot in excl_bots_mpb:
                    # Also exclude bots that have only one bot_market left
                    if len(bot[1]) > 1:
                        self.__find_arbitrage_options(bot)
            else:
                self.__logger.warning('Markets not synced yet...')

            # Update the bot_ids
            self.__update_active_bots()

            # After condition is true, print to log self is still alive
            if time.time() > self.__last_log + randint(20, 30):
                self.__logger.debug(f"Bots {self.__active_bots} are searching for arbitrage options...")
                self.__last_log = time.time()

            # Sleep, to reduce cpu usage
            time.sleep(1)


def save_and_exit():
    # TODO Implement save and backup function on user exit
    pass


if __name__ == '__main__':
    daemon_logger.info("Preparing bot startup...")

    # Initialize market locker
    market_locker = BlockedMarkets()

    # Initialize exchange APIs
    exch_clients = Exchange()

    # Create order book storage
    order_book_storage = OrderBook()

    # Create bot_markets storage
    bots_markets_storage = BotsAndMarkets()

    # Init database sync daemon
    bots_markets_daemon = BotsAndMarketsDaemon(bm_storage=bots_markets_storage)

    # Init order_book daemon
    order_book_daemon = OrderBookDaemon(
        clients=exch_clients,
        ob_storage=order_book_storage,
        bm_storage=bots_markets_storage)

    # Init trade-finder daemon (arbitrage, catch, etc..)
    trade_finder = TradeOptionsDaemon(
        clients=exch_clients,
        bm_storage=bots_markets_storage,
        ob_storage=order_book_storage,
        blocked_markets=market_locker)

    daemon_logger.info("All modules initialized. Starting bot!")

    # Let the daemons run in background
    try:
        bots_markets_daemon.start()
        order_book_daemon.start()
        time.sleep(5)
        trade_finder.start()
        trade_finder.join()
    except KeyboardInterrupt:
        daemon_logger.info('Shutdown By User')
        save_and_exit()
    finally:
        sys.exit()
