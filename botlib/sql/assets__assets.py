import threading

from botlib.sql import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR, DECIMAL


class Assets(BASE):

    __tablename__ = "assets__assets"
    id = Column(INTEGER(11), primary_key=True)
    cp_refid = Column(INTEGER(11))
    symbol = Column(INTEGER(11))
    title = Column(VARCHAR(255))
    created = Column(TINYINT(1))
    modified = Column(DECIMAL(5, 2))

    def __init__(self, bot_id, exchanges_market_id, min_profit, catch_buy_enabled, catch_buy_percent,
                 catch_sell_enabled, catch_sell_percent, balance, balance_locked, withdraw_enabled):
        self.cp_refid = bot_id
        self.symbol = exchanges_market_id
        self.title = min_profit
        self.created = catch_buy_enabled
        self.modified = catch_buy_percent


ASSETS_INSERTION_LOCK = threading.RLock()
