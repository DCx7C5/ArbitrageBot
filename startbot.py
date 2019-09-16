import sys
import time
from random import randint
from threading import Thread
from botlib.api_client.api_wrapper import Exchange
from botlib.bot_log import trade_logger
from botlib.blocked_markets import BlockedMarkets
from botlib.order_book import OrderBook, OrderBookDaemon
from botlib.bot_markets import BotsAndMarkets, BotsAndMarketsDaemon
from botlib.job_manager import ArbitrageJobThread
from botlib.sql_functions import get_all_prices_from_refid


class TradeOptionsDaemon(Thread):
    """
    Runs as daemon in background and loops through list of unique bot_ids
    to find arbitrage, catch_order, or any other trading opportunities .
    """

    def __init__(self, clients: Exchange,
                 bm_storage: BotsAndMarkets,
                 ob_storage: OrderBook,
                 blocked_markets: BlockedMarkets,
                 ):
        Thread.__init__(self)
        self.daemon = True
        self.name = f'TradeOptions'
        self.__logger = trade_logger.getChild('Arbitrage')
        self.__last_log = time.time()
        self.__bm_storage = bm_storage
        self.__ob_storage = ob_storage
        self.__market_locker = blocked_markets
        self.__active_bots = []
        self.__ec = 0
        self.__last_run = time.time()
        self.cli = clients

    def find_arbitrage_options(self, bot) -> None:
        arbitrage_options = []
        """Find arbitrage options for ALL market combinations then filters"""
        if not self.create_options_based_on_min_profit_rate(bot, arbitrage_options):
            return

    def create_options_based_on_min_profit_rate(self, bot, arbitrage_options):
        order_books = self._request_order_books_for_bot(bot)
        if not order_books:
            self.__logger.warning(order_books)
        for bids in order_books:
            for asks in order_books:
                if bids is not asks:
                    if self._check_min_profit(bids, asks):
                        arbitrage_options += [
                            {
                                'sell_market': {
                                    'exchange': bids[0],
                                    'refid': bids[1],
                                    'price': bids[2][0],
                                    'volume': bids[2][1],
                                    'limits': self.cli.get_limits(bids[0], bids[1])
                                },
                                'buy_market': {
                                    'exchange': asks[0],
                                    'refid': asks[1],
                                    'price': asks[3][0],
                                    'volume': asks[3][1],
                                    'limits': self.cli.get_limits(asks[0], asks[1])
                                }
                            }
                        ]

        if arbitrage_options:
            return True
        return False

    def _check_min_profit(self, bids, asks):
        rate_limits = self.cli.get_order_rate_limits(bids[0], bids[1])
        if (round((bids[2][0] - asks[3][0]) / bids[2][0] * 100, 2)) >= float(rate_limits['min_profit_rate']):
            return True
        return False

    def search_arbitrage_options(self, arbitrage_options):
        """Searches for arbitrage option"""
        final_order_option = None
        profit = 0
        for opt in arbitrage_options:
            if not self._check_limits_and_set_volume(opt):
                arbitrage_options.remove(opt)
                continue
            if not self._check_balances_per_option(opt):
                arbitrage_options.remove(opt)
                continue

            # Calculate profit per option
            self._calculate_profit_per_option(opt)

            if opt['profit'] > profit:
                final_order_option = opt
                profit = opt['profit']

        if final_order_option is not None:
            self.__market_locker.add_to_blocked_list(final_order_option['sell_market']['exchange'], final_order_option['sell_market']['refid'])
            self.__market_locker.add_to_blocked_list(final_order_option['buy_market']['exchange'], final_order_option['buy_market']['refid'])

        print(final_order_option)

        # if job:
        #     ArbitrageJobThread(job=[job[0], job[1]], blocked_markets=self.__market_locker, clients=self.__cli).start()
        #     self.__logger.warning(f'Order Job created! {job}')

    @staticmethod
    def _check_limits_and_set_volume(option) -> bool:
        """Calculate Order volume based on cost limits"""
        # Sell-Market:
        # if (volume * price)  on position is smaller than maximum order costs set position volume as buy volume
        # else set (max order cost / price) as order volume
        if (option['sell_market']['price'] * option['sell_market']['volume']) < option['sell_market']['limits']['maximum_order_cost']:
            sell_order_volume = option['sell_market']['volume']
        else:
            sell_order_volume = option['sell_market']['limits']['maximum_order_cost'] / option['sell_market']['price']

        # If order cost is smaller than minimum order cost return False
        if not ((sell_order_volume / option['sell_market']['price']) > option['sell_market']['limits']['minimum_order_cost']):
            return False

        # Buy-Market:
        if (option['buy_market']['price'] * option['buy_market']['volume']) < option['buy_market']['limits']['maximum_order_cost']:
            buy_order_volume = option['buy_market']['volume']
        else:
            buy_order_volume = option['buy_market']['limits']['maximum_order_cost'] / option['buy_market']['price']
        if not ((buy_order_volume / option['buy_market']['price']) > option['buy_market']['limits']['minimum_order_cost']):
            return False

        # Calculate and set final order volume for bot markets
        max_order_volume = min(sell_order_volume, buy_order_volume)
        option['sell_market']['volume'] = max_order_volume
        option['buy_market']['volume'] = max_order_volume

        # Check volume limits
        if not (option['sell_market']['limits']['minimum_order_volume'] < max_order_volume):
            return False
        if not (option['buy_market']['limits']['minimum_order_volume'] < max_order_volume):
            return False
        return True

    def _check_balances_per_option(self, option) -> bool:
        """checks sell-market and buy-market balances"""

        # Check balance sell_market
        balance_coin = self.cli.get_balance(option['sell_market']['exchange'], option['sell_market']['refid'])
        if balance_coin < option['sell_market']['volume']:
            return False

        # Check balance btc on buy market
        balance_btc = self.cli.get_balance(option['buy_market']['exchange'], 'BTC')

        if balance_btc < (option['buy_market']['volume'] * option['buy_market']['price']):
            return False
        return True

    @staticmethod
    def _calculate_profit_per_option(option):
        """Calculates most profitable arbitrage option"""

        sell_market = option['sell_market']['volume'] * option['sell_market']['price']
        buy_market = option['buy_market']['volume'] * option['buy_market']['price']
        profit = float(sell_market - buy_market)
        option.update({'profit': profit})

    def __calculate_average_prices(self, options):
        for opt in options:
            refid = opt[0][1]
            sell_prices_list = get_all_prices_from_refid(refid, 'sell')
            buy_prices_list = get_all_prices_from_refid(refid, 'buy')
            if (not sell_prices_list) or (not buy_prices_list):
                continue
            avg_sell_price = sum(sell_prices_list) / len(sell_prices_list)
            avg_buy_price = sum(buy_prices_list) / len(buy_prices_list)
            sell_price = opt[0][2]
            buy_price = opt[1][2]
            if (sell_price < avg_sell_price) or (buy_price > avg_buy_price):
                options.remove(opt)

    def _request_order_books_for_bot(self, bot) -> list:
        order_books = []
        for ob_rq in bot[1]:
            try:
                book = self.__ob_storage.get_order_book(ob_rq[0], ob_rq[1])
                order_books.append((ob_rq[0], ob_rq[1], book[0][0], book[1][0]))
            except TypeError:
                time.sleep(3)
                self.__logger.warning('Markets not synced yet...')
                self._request_order_books_for_bot(bot)
        return order_books



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
                        self.find_arbitrage_options(bot)
            else:
                self.__logger.warning('Markets not synced yet...')

            # Update the bot_ids
            self.__update_active_bots()

            # After condition is true, print to log if self is still alive
            if time.time() > self.__last_log + randint(20, 30):
                self.__logger.debug(f"Bots {self.__active_bots} are searching for arbitrage options...")
                self.__last_log = time.time()

            # Sleep, to reduce cpu usage
            time.sleep(.61)


def save_and_exit():
    # TODO Implement save and backup function on user exit
    pass


if __name__ == '__main__':
    trade_logger.info("Preparing bot startup...")

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
        blocked_markets=market_locker
    )

    trade_logger.info("All modules initialized. Starting bot!")

    # Let the daemons run in background
    try:
        bots_markets_daemon.start()
        order_book_daemon.start()
        time.sleep(5)
        trade_finder.start()
        trade_finder.join()
    except KeyboardInterrupt:
        trade_logger.info('Shutdown By User')
        save_and_exit()
    finally:
        sys.exit()
