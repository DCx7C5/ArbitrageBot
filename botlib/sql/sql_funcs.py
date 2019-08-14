from pprint import pprint

from botlib.sql.bots_sql import Bots
from botlib.sql.exchanges_sql import Exchanges
from botlib.sql import BASE, SESSION, CONNECTION
from botlib.sql.bot_markets_sql import BotMarkets
from botlib.sql.jobs_sql import Jobs
from botlib.sql.orders_sql import Orders
from botlib.sql.exchanges_sql import Exchanges


def market_from_exchange(exchange):
    try:
        (eid, ) = SESSION.query(Exchanges.id).filter(Exchanges.name == exchange).all()[0]
        return [x.to_dict() for x in SESSION.query(BotMarkets).filter(BotMarkets.exchange_id == eid).all()]
    finally:
        SESSION.close()


def get_table(table):
    if table == Bots.__tablename__:
        table = Bots
    elif table == 'botmarkets':
        table = BotMarkets
    elif table == Jobs.__tablename__:
        table = Jobs
    elif table == Orders.__tablename__:
        table = Orders
    elif table == Exchanges.__tablename__:
        table = Exchanges
    try:
        return [x.to_dict() for x in SESSION.query(table).all()]
    finally:
        SESSION.close()


def get_table_columns(table):
    if table == Bots.__tablename__:
        table = Bots
    elif table == 'botmarkets':
        table = BotMarkets
    elif table == Jobs.__tablename__:
        table = Jobs
    elif table == Orders.__tablename__:
        table = Orders
    elif table == Exchanges.__tablename__:
        table = Exchanges
    try:
        return [x.to_dict().keys() for x in SESSION.query(table).all()]
    finally:
        SESSION.close()


def get_actual_bot_markets(bid):
    return CONNECTION.execute(
            f'SELECT (SELECT name FROM arbitrage.exchanges '
            f'WHERE bot_markets.exchange_id = exchanges.id),refid'
            f' FROM arbitrage.bot_markets'
            f' WHERE bot_id={bid}').fetchall()


def get_trading_limits_with_refid(ref_id):
    try:
        return [x.to_dict() for x in SESSION.query(BotMarkets).filter(BotMarkets.refid == ref_id).all()]

    finally:
        SESSION.close()

