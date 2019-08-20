import threading

from botlib.sql import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR, DECIMAL


class BotsExchangesMarkets(BASE):

    __tablename__ = "arbitrage__bots_exchanges_markets"
    id = Column(INTEGER(11), primary_key=True)
    bot_id = Column(INTEGER(11))
    exchanges_market_id = Column(INTEGER(11))
    min_profit = Column(VARCHAR(255))
    catch_buy_enabled = Column(TINYINT(1))
    catch_buy_percent = Column(DECIMAL(5, 2))
    catch_sell_enabled = Column(TINYINT(1))
    catch_sell_percent = Column(DECIMAL(5, 2))
    balance = Column(VARCHAR(255))
    balance_locked = Column(VARCHAR(255))
    withdraw_enabled = Column(INTEGER(1))

    def __init__(self, bot_id, exchanges_market_id, min_profit, catch_buy_enabled, catch_buy_percent,
                 catch_sell_enabled, catch_sell_percent, balance, balance_locked, withdraw_enabled):
        self.bot_id = bot_id
        self.exchanges_market_id = exchanges_market_id
        self.min_profit = min_profit
        self.catch_buy_enabled = catch_buy_enabled
        self.catch_buy_percent = catch_buy_percent
        self.catch_sell_enabled = catch_sell_enabled
        self.catch_sell_percent = catch_sell_percent
        self.balance = balance
        self.balance_locked = balance_locked
        self.withdraw_enabled = withdraw_enabled


BEM_INSERTION_LOCK = threading.RLock()
