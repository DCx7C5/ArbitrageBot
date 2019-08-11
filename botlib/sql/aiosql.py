import asyncio
import sys
import time

from aiomysql import create_pool, Pool, Connection, connect
_GET_KEY_AND_SECRET = "SELECT exchanges.key, exchanges.secret FROM arbitrage.exchanges WHERE active=1"
_GET_BOT_MARKETS_TABLE = "SELECT * FROM arbitrage.bot_markets"
_GET_BOTS_TABLE = "SELECT * FROM arbitrage.bots"
_GET_EXCHANGES_TABLE = "SELECT * FROM arbitrage.exchanges"
_GET_ACTIVE_BOT_MARKETS = """SELECT * FROM arbitrage.bot_markets WHERE exchange_id NOT IN
 (SELECT id FROM arbitrage.exchanges WHERE active=0) AND bot_id NOT IN 
 (SELECT id FROM arbitrage.bots WHERE enabled=0) AND enabled=1;"""


async def initialize_mysql_pool(loop) -> Pool:
    return await create_pool(host='127.0.0.1', port=3306,
                             user='backend', password='password',
                             db='arbitrage', loop=loop,
                             echo=True, minsize=4, maxsize=10,
                             autocommit=True)


async def initialize_mysql_connection(loop) -> Connection:
    return await connect(host='127.0.0.1', port=3306,
                         user='backend', password='password',
                         db='arbitrage', loop=loop,
                         echo=True, autocommit=True)


async def get_bot_markets_table(conn):
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


async def get_active_bot_markets(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_ACTIVE_BOT_MARKETS)
        return await cur.fetchall()


async def get_key_and_secrets(conn):
    async with conn.cursor() as cur:
        await cur.execute(_GET_KEY_AND_SECRET)
        return await cur.fetchall()
