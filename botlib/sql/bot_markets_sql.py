import threading
import time

from botlib.sql import BASE, SESSION
from sqlalchemy import Column, Table
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR


class BotMarkets(BASE):

    __tablename__ = "bot_markets"
    id = Column(INTEGER(11), primary_key=True)
    bot_id = Column(INTEGER(11))
    exchange_id = Column(INTEGER(11))
    enabled = Column(TINYINT(1))
    refid = Column(VARCHAR(255))
    symbol = Column(VARCHAR(255))
    min_size = Column(VARCHAR(255))
    max_size = Column(VARCHAR(255))
    min_profit = Column(VARCHAR(255))

    def __init__(self, bot_id, exchange_id, enabled, refid, symbol, min_size, max_size, min_profit):
        self.bot_id = bot_id
        self.exchange_id = exchange_id
        self.enabled = enabled
        self.refid = refid
        self.symbol = symbol
        self.min_size = min_size
        self.max_size = max_size
        self.min_profit = min_profit

    def to_dict(self):
        return {
            "bot_id": self.bot_id,
            "exchange_id": self.exchange_id,
            "enabled": self.enabled,
            "refid": self.refid,
            "symbol": self.symbol,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "min_profit": self.min_profit
            }


INSERTION_LOCK = threading.RLock()


def get_bot_markets_sql(active=False):
    try:
        if active:
            return [x.to_dict() for x in SESSION.query(BotMarkets).filter(BotMarkets.enabled == 1).all()]
        return [x.to_dict() for x in SESSION.query(BotMarkets).all()]
    finally:
        SESSION.close()


def get_bot_market_sql(bot_id):
    try:
        return [x.to_dict() for x in SESSION.query(BotMarkets).filter(BotMarkets.bot_id == bot_id).all()][0]
    finally:
        SESSION.close()


st = time.time()
for r in range(10000):
    get_bot_market_sql(1)
print(time.time() - st)
