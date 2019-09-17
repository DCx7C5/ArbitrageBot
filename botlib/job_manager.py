import time
from threading import Thread
from botlib.blocked_markets import BlockedMarkets
from botlib.bot_log import daemon_logger
from botlib.api_client.api_wrapper import Exchange
from botlib.sql_functions import create_order_sql, update_order_sql, get_bot_id_from_refid


class ArbitrageJobThread(Thread):

    def __init__(self, job, blocked_markets: BlockedMarkets, clients: Exchange):
        Thread.__init__(self)
        self.name = f'OrderThread'
        self.job = job
        self.logger = daemon_logger

        self.sell_market = self.job['sell_market']
        self.buy_market = self.job['buy_market']

        self.sell_order_done = False
        self.sell_order_error_count = 0
        self.buy_order_done = False
        self.buy_order_error_count = 0

        self.bot_id = get_bot_id_from_refid(
            refid=self.sell_market['refid']
        )

        self.blocked_markets = blocked_markets
        self.cli = clients

    def __save_job_in_database(self):
        pass

    def sell_order_process(self):
        self.logger.debug(f'Starting create_sell_order procedure')

        order = self.cli.create_limit_order(
            exchange=self.sell_market['exchange'],
            ref_id=self.sell_market['refid'],
            side='sell',
            price=self.sell_market['price'],
            volume=self.sell_market['volume']
        )
        if not order:
            return False

        # Save to database
        create_order_sql(
            bot_id=self.bot_id,
            order_id=order["order_id"],
            status=order["status"],
            side='sell',
            refid=self.sell_market['refid'],
            price=order["price"],
            volume=order["volume"],
            executed_volume=order["executed_volume"],
            created=order['created'],
            modified=order['modified']
        )

        self.logger.debug("Order saved in Database")
        while not self.sell_order_done:
            order_check = self.cli.get_order_status(
                exchange=self.sell_market['exchange'],
                order_id=self.sell_market['order_id'],
                refid=self.sell_market['refid']
            )

    def run(self) -> None:
        self.logger.warning("Starting Job Thread!")

        if sell_order['status'] != "done":
            time.sleep(0.39)
        sell_order = self.__update_order_for_market_side(exchange=self.job[0][0], order_id=sell_order['order_id'])
        if sell_order['status'] != "done":
            self.cli.cancel_order(exchange=sell_order["exchange"], order_id=sell_order["order_id"])
            self.logger.warning("Canceled order")
            return
        elif sell_order['status'] == "done":
            buy_order = self.__do_order_for_market_side(self.job[1], side='buy')
            if buy_order['status'] != "done":
                time.sleep(0.39)
            buy_order = self.__update_order_for_market_side(exchange=self.__job[1][0], order_id=buy_order['order_id'])
            if buy_order['status'] != "done":
                self.cli.cancel_order(exchange=buy_order["exchange"], order_id=buy_order["order_id"])
                self.logger.warning("Canceled order")
                return
            elif buy_order['status'] == "done":
                self.__save_job_in_database()
                self.blocked_markets.remove_from_blocked_list(
                    exchange=self.sell_market['exchange'],
                    refid=self.sell_market['refid']
                )
                self.blocked_markets.remove_from_blocked_list(
                    exchange=self.buy_market['exchange'],
                    refid=self.buy_market['refid']
                )
                self.logger.debug("Bot markets removed from block list")

                return
