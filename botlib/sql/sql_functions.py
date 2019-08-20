import time

from sqlalchemy import func

from botlib.sql import SESSION, CONNECTION
from botlib.sql.bots import Bots
from botlib.sql.bot_markets import BotMarkets
from botlib.sql.exchanges import Exchanges
from botlib.sql.jobs import JOB_INSERTION_LOCK, Jobs
from botlib.sql.orders import ORDER_INSERTION_LOCK, Orders


def get_enabled_bots_ids() -> list:
    try:
        return [x[0] for x in SESSION.query(Bots.id).filter(Bots.enabled == 1).all()]
    finally:
        SESSION.close()


def get_active_bot_markets_sql(bot_ids: list) -> list:
    try:
        bot_ids = tuple(bot_ids)
        return CONNECTION.execute(f"SELECT bot_id, name, refid FROM arbitrage.bot_markets JOIN arbitrage.exchanges ON exchange_id = exchanges.id AND bot_id IN {bot_ids}").fetchall()
    finally:
        SESSION.close()


def get_key_and_secret(exchange):
    try:
        return SESSION.query(Exchanges.key, Exchanges.secret).filter(Exchanges.name == exchange).all()[0]
    finally:
        SESSION.close()


def get_jobs():
    try:
        return [x.to_dict() for x in SESSION.query(Jobs).all()]
    finally:
        SESSION.close()


def update_job(bot_id, profit, profit_percent, sell_order_id, buy_order_id, created):
    with JOB_INSERTION_LOCK:

        job0 = SESSION.query(Jobs).get(sell_order_id)
        job1 = SESSION.query(Jobs).get(buy_order_id)

        if not job0 and not job1:
            job = Jobs(
                bot_id=bot_id,
                profit=profit,
                profit_percent=profit_percent,
                sell_order_id=sell_order_id,
                buy_order_id=buy_order_id,
                created=created
            )
            SESSION.add(job)
            SESSION.flush()
        SESSION.commit()


def update_market_job(bot_id, profit, profit_percent, buy_bot_market_id, sell_bot_market_id, created):
    with JOB_INSERTION_LOCK:

        job0 = SESSION.query(Jobs).get(buy_bot_market_id)
        job1 = SESSION.query(Jobs).get(sell_bot_market_id)

        if not job0 and not job1:
            job = Jobs(
                bot_id=bot_id,
                profit=profit,
                profit_percent=profit_percent,
                buy_bot_market_id=buy_bot_market_id,
                sell_bot_market_id=sell_bot_market_id,
                created=created
            )
            SESSION.add(job)
            SESSION.flush()
        SESSION.commit()


def update_order(bot_market_id, refid,
                 status, side, price, volume, executed_volume):

    with ORDER_INSERTION_LOCK:

        order = SESSION.query(Orders).get(bot_market_id)

        if not order:
            order = Orders(bot_market_id, refid, status, side, price, volume, executed_volume)
            SESSION.add(order)
            SESSION.flush()
        else:
            order.status = status
            order.price = price
            order.volume = volume
            order.executed_volume = volume
        SESSION.commit()
