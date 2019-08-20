import time
from threading import RLock

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, DATETIME, VARCHAR

from botlib.sql import BASE


class Jobs(BASE):

    __tablename__ = "jobs"
    id = Column(INTEGER(11), primary_key=True)
    bot_id = Column(INTEGER(11))
    buy_bot_market_id = Column(INTEGER(11))
    sell_bot_market_id = Column(INTEGER(11))
    buy_order_id = Column(INTEGER(11))
    sell_order_id = Column(INTEGER(11))
    profit = Column(VARCHAR(255))
    profit_percent = Column(VARCHAR(255))
    created = Column(DATETIME)
    closed = Column(DATETIME)

    def __init__(self, bot_id, profit, profit_percent, buy_bot_market_id=0, buy_order_id=0,
                 created=None, sell_bot_market_id=0, sell_order_id=0):
        self.bot_id = bot_id
        self.profit = profit
        self.profit_percent = profit_percent

        if sell_bot_market_id and buy_bot_market_id:
            self.sell_bot_market_id = sell_bot_market_id
            self.buy_bot_market_id = buy_bot_market_id
            self.sell_order_id = 0
            self.buy_order_id = 0
            print(1)

        elif sell_order_id and buy_order_id:
            self.sell_order_id = sell_order_id
            self.buy_order_id = buy_order_id
            self.sell_bot_market_id = 0
            self.buy_bot_market_id = 0
            print(2)

        if created is not None:
            self.created = created
        self.closed = time.strftime('%Y-%m-%d %H:%M:%S')
        print(self.created, self.closed)

    def to_dict(self):
        return {
            "bot_id": self.bot_id,
            "profit": self.profit,
            "profit_percent": self.profit_percent,
            "buy_bot_market_id": self.buy_bot_market_id,
            "sell_bot_market_id": self.sell_bot_market_id,
            "buy_order_id": self.buy_order_id,
            "sell_order_id": self.sell_order_id,
            "created": self.created,
            "closed":  self.closed
            }


JOB_INSERTION_LOCK = RLock()
