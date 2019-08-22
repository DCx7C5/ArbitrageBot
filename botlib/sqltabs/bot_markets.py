import threading

from botlib.sqltabs import BASE, SESSION
from sqlalchemy import Column
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
            'id': self.id,
            "bot_id": self.bot_id,
            "exchange_id": self.exchange_id,
            "enabled": self.enabled,
            "refid": self.refid,
            "symbol": self.symbol,
            "min_size": self.min_size,
            "max_size": self.max_size,
            "min_profit": self.min_profit
            }
