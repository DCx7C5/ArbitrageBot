import time
from threading import RLock

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, DATETIME, VARCHAR

from botlib.sql import BASE, SESSION


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


Jobs.__table__.create(checkfirst=True)
JOB_INSERTION_LOCK = RLock()


def get_jobs():
    try:
        return [x.to_dict() for x in SESSION.query(Jobs).all()]
    finally:
        SESSION.close()


def update_job(bot_id, profit, profit_percent, sell_order_id, buy_order_id, created):
    with JOB_INSERTION_LOCK:

        job0 = SESSION.query(Jobs).get(sell_order_id)
        job1 = SESSION.query(Jobs).get(buy_order_id)

        if not job0 and not job1:
            job = Jobs(
                bot_id=bot_id,
                profit=profit,
                profit_percent=profit_percent,
                sell_order_id=sell_order_id,
                buy_order_id=buy_order_id,
                created=created
            )
            SESSION.add(job)
            SESSION.flush()
        SESSION.commit()


def update_market_job(bot_id, profit, profit_percent, buy_bot_market_id, sell_bot_market_id, created):
    with JOB_INSERTION_LOCK:

        job0 = SESSION.query(Jobs).get(buy_bot_market_id)
        job1 = SESSION.query(Jobs).get(sell_bot_market_id)

        if not job0 and not job1:
            job = Jobs(
                bot_id=bot_id,
                profit=profit,
                profit_percent=profit_percent,
                buy_bot_market_id=buy_bot_market_id,
                sell_bot_market_id=sell_bot_market_id,
                created=created
            )
            SESSION.add(job)
            SESSION.flush()
        SESSION.commit()
