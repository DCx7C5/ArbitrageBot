import pymysql.cursors

# Connect to the database
connection = pymysql.connect(host='localhost',
                             user='backend',
                             password='password',
                             db='arbitrage',
                             )
connection.autocommit_mode = True


def get_enabled_bots_ids():
    with connection.cursor() as curs:
        curs.execute(f'SELECT bots.id FROM arbitrage.bots WHERE enabled = 1')
        return [item[0] for item in curs.fetchall()]


def get_enabled_exchanges():
    with connection.cursor() as curs:
        curs.execute(f'SELECT name FROM arbitrage.exchanges WHERE enabled = 1')
        return [item[0] for item in curs.fetchall()]


def get_enabled_bot_markets_sql(bot_ids: list or tuple):
    with connection.cursor() as curs:
        curs.execute(f'SELECT bot_id, name, refid FROM arbitrage.bot_markets '
                     f'JOIN arbitrage.exchanges ON exchange_id = exchanges.id '
                     f'AND arbitrage.exchanges.enabled = 1 '
                     f'AND bot_id IN {bot_ids}')
        return curs.fetchall()


def get_key_and_secret(exchange: str):
    with connection.cursor() as curs:
        curs.execute(f"SELECT exchanges.key, exchanges.secret FROM exchanges "
                     f"WHERE exchanges.name = %s ", exchange)
        return curs.fetchone()


def get_open_orders():
    pass
