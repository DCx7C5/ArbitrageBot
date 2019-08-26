import threading
from pymysqlpool import ConnectionPool

connection = ConnectionPool(host='127.0.0.1',
                            user='backend',
                            password='password',
                            db='arbitrage',
                            autocommit=True,
                            size=5)

INSERTION_LOCK_BOT_MARKETS = threading.RLock()


def disable_orphaned_bot_market_sql(bot_id: int):
    with connection.get_connection() as curs:
        with INSERTION_LOCK_BOT_MARKETS:
            curs.execute(
                f'UPDATE bots SET enabled = 0 WHERE bots.id = {int(bot_id)}'
            )
        return True


def get_enabled_bots_ids_sql():
    with connection.get_connection() as curs:
        curs.execute(
            'SELECT bots.id FROM arbitrage.bots '
            'WHERE bots.enabled = 1'
        )
        return [item[0] for item in curs.fetchall()]


def get_enabled_exchanges_sql():
    with connection.get_connection() as curs:
        curs.execute(
            'SELECT name FROM arbitrage.exchanges '
            'WHERE exchanges.enabled = 1'
        )
        return [item[0] for item in curs.fetchall()]


def get_enabled_bot_markets_sql(bot_ids):
    bot_ids = tuple(bot_ids)
    with connection.get_connection() as curs:
        curs.execute(
            """SELECT bot_id, name, refid FROM arbitrage.bot_markets 
            JOIN arbitrage.exchanges ON exchange_id = exchanges.id
            AND exchanges.enabled = 1 AND bot_markets.enabled = 1 AND bot_id IN {0};""".format(bot_ids)
        )
        return curs.fetchall()


def get_key_and_secret_sql(exchange: str):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT exchanges.key, exchanges.secret FROM exchanges "
            "WHERE exchanges.name = %s ", exchange
        )
        return curs.fetchone()


def get_one_symbol_from_exchange_sql(exchange, refid):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT symbol From bot_markets WHERE refid = %s AND exchange_id = (SELECT id FROM exchanges WHERE name = %s)", (refid, exchange, )
        )
        return curs.fetchall()


def get_symbols_for_exchange_sql(exchange):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT symbol, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return curs.fetchall()


def get_min_profit_for_exchange_sql(exchange):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT min_profit, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return [(float(x), y) for x, y in curs.fetchall()]


def get_max_order_size_for_exchange_sql(exchange):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT max_size, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return [(float(x), y) for x, y in curs.fetchall()]

