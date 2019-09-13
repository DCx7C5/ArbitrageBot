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
        return curs.fetchone()[0]


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
            "SELECT max_cost, refid From bot_markets WHERE exchange_id = (SELECT id FROM exchanges WHERE name = %s)", exchange
        )
        return [(float(x), y) for x, y in curs.fetchall()]


def get_refid_from_order_id(order_id):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT refid From orders WHERE order_id = %s ", order_id
        )
        return curs.fetchone()[0]


def create_order_sql(bot_id, order_id, status, side, refid, price, volume, executed_volume, created, modified):
    with connection.get_connection() as curs:
        curs.execute(
            "INSERT INTO arbitrage.orders(bot_id, order_id, status, side, refid, price, volume, executed_volume, created, modified)"
            " VALUES (%d, %d, %s, %s, %s, %s, %s, %s, %s, %s)", (int(bot_id), int(order_id), status, side, refid, price, volume, executed_volume, created, modified)
        )
    return True


def update_order_sql(order_id, status, price, volume, executed_volume, created, modified):
    with connection.get_connection() as curs:
        curs.execute(
            "UPDATE arbitrage.orders "
            "SET created = %s, modified = %s, status = %s, executed_volume = %s, price = %s, volume = %s WHERE order_id = %d",
            (created, modified, status, executed_volume, price, volume, order_id,)
        )
    return True


def create_job():
    with connection.get_connection() as curs:
        curs.execute(
            ""
        )


def get_all_prices_from_refid(refid, side):
    with connection.get_connection() as curs:
        curs.execute(
            """SELECT price from orders
                JOIN bot_markets bm on orders.bot_id = bm.bot_id
                JOIN bots b on bm.bot_id = b.id
                JOIN exchanges e on bm.exchange_id = e.id
                WHERE bm.refid = %s AND side = %s;""", (refid, side,)
        )
    prices = [i[0] for i in curs.fetchall()]
    if not prices:
        return None
    return prices


def get_bot_id_from_refid(refid):
    with connection.get_connection() as curs:
        curs.execute(
            """SELECT bot_id from bot_markets
                JOIN exchanges e on bot_markets.exchange_id = e.id
                JOIN bots b on bot_markets.bot_id = b.id
                WHERE refid = %s;""", (refid,)
        )
    return curs.fetchone()[0]


def get_deposit_address_sql(exchange, refid):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT deposit_address FROM bot_markets "
            "JOIN exchanges e on bot_markets.exchange_id = e.id "
            "WHERE refid = %s AND e.name = %s", (refid, exchange,)
        )
    return curs.fetchone()[0]


def get_market_data_sql(exchange):
    with connection.get_connection() as curs:
        curs.execute(
            "SELECT refid, max_cost, min_profit, deposit_address FROM bot_markets "
            "JOIN exchanges e on bot_markets.exchange_id = e.id "
            "WHERE e.name = %s", (exchange, )
        )
    return [{'refid': i[0], 'max_size': i[1], 'min_profit': i[2], 'deposit': i[3]} for i in curs.fetchall()]
