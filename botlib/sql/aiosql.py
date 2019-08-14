import asyncio
import time

from aiomysql import Connection
from aiomysql import create_pool
from aiomysql import connect


_GET_KEY_AND_SECRET = "SELECT exchanges.key, exchanges.secret FROM arbitrage.exchanges WHERE active=1"
_GET_BOT_MARKETS_TABLE = "SELECT * FROM arbitrage.bot_markets"
_GET_BOTS_TABLE = "SELECT * FROM arbitrage.bots"
_GET_EXCHANGES_TABLE = "SELECT * FROM arbitrage.exchanges"
_GET_ACTIVE_EXCHANGES = "SELECT * FROM arbitrage.exchanges WHERE active=1"
_GET_ACTIVE_BOT_MARKETS = """SELECT * FROM arbitrage.bot_markets WHERE exchange_id NOT IN
 (SELECT id FROM arbitrage.exchanges WHERE active=0) AND bot_id NOT IN 
 (SELECT id FROM arbitrage.bots WHERE enabled=0) AND enabled=1;"""


async def initialize_mysql_pool(loop) -> Connection:
    pool = await create_pool(host='127.0.0.1', port=3306,
                             user='backend', password='password',
                             db='arbitrage', loop=loop,
                             echo=True, minsize=4, maxsize=10,
                             autocommit=True)
    async with pool.acquire() as conn:
        return conn


async def initialize_mysql_connection(loop) -> Connection:
    return await connect(host='127.0.0.1', port=3306,
                         user='backend', password='password',
                         db='arbitrage', loop=loop,
                         echo=True, autocommit=True)


async def get_bot_markets_table(conn: Connection) -> list:
    async with conn.cursor() as cur:
        await cur.execute(_GET_BOT_MARKETS_TABLE)
        return await cur.fetchall()


async def get_bots_table(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_BOTS_TABLE)
        return await cur.fetchall()


async def get_exchanges_table(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_EXCHANGES_TABLE)
        return await cur.fetchall()


async def get_active_exchanges(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_ACTIVE_EXCHANGES)
        return await cur.fetchall()


async def get_active_bot_markets(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_ACTIVE_BOT_MARKETS)
        return await cur.fetchall()


async def get_key_and_secrets(conn, exchange):
    async with conn.cursor() as cur:
        await cur.execute(_GET_KEY_AND_SECRET + f" AND name='{exchange}'")
        res = await cur.fetchall()
        return res[0]


def test():
    async def _test():
        t1 = time.time()
        conn = await initialize_mysql_connection(asyncio.get_running_loop())
        await get_key_and_secrets(conn, "graviex")
        await get_active_bot_markets(conn)
        await get_exchanges_table(conn)
        await get_bots_table(conn)
        await get_bot_markets_table(conn)
        t2 = time.time()
        print("Single connection: " + str(t2 - t1))
        conn = await initialize_mysql_pool(asyncio.get_running_loop())
        await get_key_and_secrets(conn, "crex")
        await get_active_bot_markets(conn)
        await get_exchanges_table(conn)
        await get_bots_table(conn)
        await get_bot_markets_table(conn)
        print("Pool connection: " + str(time.time() - t2))
    asyncio.run(_test())
