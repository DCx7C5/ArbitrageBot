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
        self.sell_market = self.job[0]
        self.sell_exchange = self.sell_market[0]
        self.sell_refid = self.sell_market[1]
        self.sell_price = self.sell_market[2]
        self.sell_amount = self.sell_market[-1]
        self.sell_order_done = False
        self.sell_order_successful = False
        self.buy_market = self.job[1]
        self.buy_order_done = False
        self.buy_order_successful = False
        self.bot_id = get_bot_id_from_refid(refid=self.sell_market[1])
        self.blocked_markets = blocked_markets
        self.logger = daemon_logger
        self.cli = clients

    def __save_job_in_database(self):
        pass

    def __do_sell_order_for_market(self):
        self.logger.debug('Starting sell order procedure')


    def __do_order_for_market_side(self, market_side, side):
        self.logger.debug(f"Starting create order procedure on {side} market")
        # Create Order
        exchange = market_side[0]
        ref_id = market_side[1]
        order = self.cli.create_limit_order(
            exchange=exchange,
            ref_id=ref_id,
            side=side,
            price=market_side[2],
            volume=market_side[4]
        )
        self.logger.debug(f"Created order on {side} market")

        bot_id = get_bot_id_from_refid(ref_id)
        # Save to database
        create_order_sql(bot_id, order["order_id"], order["status"], side, ref_id, order["price"], order["volume"], order["executed_volume"])
        self.logger.debug("Order saved in Database")
        return [
            order["order_id"],
            order["refid"],
            order["status"],
            order['side'],
            order['price'],
            order['volume'],
            order['executed_volume'],
            exchange
        ]

    def __update_order_for_market_side(self, exchange, order_id):
        # Update Order
        order_check = self.cli.get_order_status(
            exchange=exchange,
            order_id=order_id
        )
        self.logger.debug(f"Updated order status for {order_check['side']} market")

        # Update Database
        update_order_sql(
            status=order_check["status"],
            executed_volume=order_check["executed_volume"],
            order_id=order_id
        )
        self.logger.debug("Saved updated order status to database")
        return {
            'order_id': order_id,
            'status': order_check["status"],
            'exec_vol': order_check["executed_volume"],
            'exchange': exchange,
            'side': order_check['side']
        }

    def run(self) -> None:
        self.logger.warning("Starting Job Thread!")
        sell_order = self.__do_order_for_market_side(self.__job[0], side='sell')
        if sell_order['status'] != "done":
            time.sleep(0.39)
        sell_order = self.__update_order_for_market_side(exchange=self.__job[0][0], order_id=sell_order['order_id'])
        if sell_order['status'] != "done":
            self.cli.cancel_order(exchange=sell_order["exchange"], order_id=sell_order["order_id"])
            self.logger.warning("Canceled order")
            return
        elif sell_order['status'] == "done":
            buy_order = self.__do_order_for_market_side(self.__job[1], side='buy')
            if buy_order['status'] != "done":
                time.sleep(0.39)
            buy_order = self.__update_order_for_market_side(exchange=self.__job[1][0], order_id=buy_order['order_id'])
            if buy_order['status'] != "done":
                self.cli.cancel_order(exchange=buy_order["exchange"], order_id=buy_order["order_id"])
                self.logger.warning("Canceled order")
                return
            elif buy_order['status'] == "done":
                self.__save_job_in_database()
                self.blocked_markets.remove_from_blocked_list(exchange=sell_order['exchange'], refid=self.__job[0][1])
                self.blocked_markets.remove_from_blocked_list(exchange=buy_order['exchange'], refid=self.__job[1][1])
                self.logger.debug("Bot markets removed from block list")

                return
