from botlib.sql import SESSION, CONNECTION


def get_enabled_bots_ids() -> tuple:
    try:
        return tuple([x[0] for x in CONNECTION.execute(
            f'SELECT id FROM arbitrage.bots '
            f'WHERE enabled = 1'
        ).fetchall()])
    finally:
        SESSION.close()


def get_enabled_exchanges() -> tuple:
    try:
        return tuple([x[0] for x in CONNECTION.execute(
            f'SELECT name FROM arbitrage.exchanges '
            f'WHERE enabled = 1'
        ).fetchall()])
    finally:
        SESSION.close()


def get_enabled_bot_markets_sql(bot_ids: list or tuple) -> list:
    try:
        bot_ids = tuple(bot_ids)
        return CONNECTION.execute(
            f'SELECT bot_id, name, refid FROM arbitrage.bot_markets '
            f'JOIN arbitrage.exchanges ON exchange_id = exchanges.id '
            f'AND arbitrage.exchanges.enabled = 1 '
            f'AND bot_id IN {bot_ids}').fetchall()
    finally:
        SESSION.close()


def get_key_and_secret(exchange: str) -> tuple:
    try:
        return CONNECTION.execute(
            f"SELECT exchanges.key, exchanges.secret FROM exchanges "
            f"WHERE exchanges.name = %s ", exchange
        ).fetchone()
    finally:
        SESSION.close()


def get_open_orders():
    pass
