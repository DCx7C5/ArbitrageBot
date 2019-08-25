import pymysql
import threading

connection = pymysql.connect(host='127.0.0.1',
                             user='backend',
                             password='password',
                             db='arbitrage',
                             autocommit=True)

INSERTION_LOCK = threading.RLock()


def get_enabled_bots_ids_sql():
    with connection.cursor() as curs:
        curs.execute(
            'SELECT bots.id FROM arbitrage.bots '
            'WHERE bots.enabled = 1'
        )
        return [item[0] for item in curs.fetchall()]


def get_enabled_exchanges_sql():
    with connection.cursor() as curs:
        curs.execute(
            'SELECT name FROM arbitrage.exchanges '
            'WHERE exchanges.enabled = 1'
        )
        return [item[0] for item in curs.fetchall()]


def get_enabled_bot_markets_sql(bot_ids):
    bot_ids = tuple(bot_ids)
    with connection.cursor() as curs:
        curs.execute(
            """SELECT bot_id, name, refid FROM arbitrage.bot_markets 
            JOIN arbitrage.exchanges ON exchange_id = exchanges.id
            AND exchanges.enabled = 1 AND bot_markets.enabled = 1 AND bot_id IN {0};""".format(bot_ids)
        )
        return curs.fetchall()


def get_key_and_secret_sql(exchange: str):
    with connection.cursor() as curs:
        curs.execute(
            "SELECT exchanges.key, exchanges.secret FROM exchanges "
            "WHERE exchanges.name = %s ", exchange
        )
        return curs.fetchone()


def get_symbols_for_exchange_sql(exchange):
    with connection.cursor() as curs:
        curs.execute(
            "SELECT symbol, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return curs.fetchall()


def get_min_profit_for_exchange_sql(exchange):
    with connection.cursor() as curs:
        curs.execute(
            "SELECT min_profit, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return [(float(x), y) for x, y in curs.fetchall()]


def get_max_order_size_for_exchange_sql(exchange):
    with connection.cursor() as curs:
        curs.execute(
            "SELECT max_size, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return [(float(x), y) for x, y in curs.fetchall()]


def get_open_orders():
    pass
