import threading

from botlib.sqltabs import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR, DATETIME, DECIMAL


class Bots(BASE):

    __tablename__ = "arbitrage__bots"
    id = Column(INTEGER(11), primary_key=True)
    version = Column(INTEGER(1))
    user_id = Column(INTEGER(11))
    enabled = Column(TINYINT(1))
    title = Column(VARCHAR(255))
    min_profit_percent = Column(VARCHAR(255))
    catch_order_enabled = Column(TINYINT(1))
    balance = Column(VARCHAR(255))
    balance_available = Column(VARCHAR(255))
    balance_transfer = Column(VARCHAR(255))
    balance_locked = Column(VARCHAR(255))
    balance_btc = Column(VARCHAR(255))
    highest_balance = Column(VARCHAR(255))
    initial_balance = Column(VARCHAR(255))
    initial_avg_price = Column(VARCHAR(255))
    last_price = Column(VARCHAR(255))
    last_run = Column(DATETIME)
    balance_increase_share = Column(DECIMAL(5, 2))
    auto_withdraw_enabled = Column(TINYINT(1))
    status = Column(VARCHAR(255))
    created = Column(DATETIME)
    last_balance_update = Column(INTEGER(32))

    def __init__(self, version, user_id, enabled, title, min_profit_percent, catch_order_enabled, balance,
                 balance_available, balance_transfer, balance_locked, balance_btc, highest_balance, initial_balance,
                 initial_avg_price, last_price, last_run, balance_increase_share, auto_withdraw_enabled,
                 status, created, last_balance_update):
        self.version = version
        self.user_id = user_id
        self.enabled = enabled
        self.title = title
        self.min_profit_percent = min_profit_percent
        self.catch_order_enabled = catch_order_enabled
        self.balance = balance
        self.balance_available = balance_available
        self.balance_transfer = balance_transfer
        self.balance_locked = balance_locked
        self.balance_btc = balance_btc
        self.highest_balance = highest_balance
        self.initial_balance = initial_balance
        self.initial_avg_price = initial_avg_price
        self.last_price = last_price
        self.last_run = last_run
        self.balance_increase_share = balance_increase_share
        self.auto_withdraw_enabled = auto_withdraw_enabled
        self.status = status
        self.created = created
        self.last_balance_update = last_balance_update


BOTS_INSERTION_LOCK = threading.RLock()
