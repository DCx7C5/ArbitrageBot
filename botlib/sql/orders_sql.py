import threading
import time

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, DATETIME

from botlib.sql import BASE, SESSION


class Orders(BASE):

    __tablename__ = "orders"
    id = Column(INTEGER(11), primary_key=True)
    bot_market_id = Column(INTEGER(11))
    refid = Column(VARCHAR(255))
    status = Column(VARCHAR(255))
    side = Column(VARCHAR(255))
    price = Column(VARCHAR(255))
    volume = Column(VARCHAR(255))
    executed_volume = Column(VARCHAR(255))
    created = Column(DATETIME)
    modified = Column(DATETIME)

    def __init__(self, bot_market_id, refid, status, side, price, volume, executed_volume, timestamp):
        self.bot_market_id = bot_market_id
        self.refid = refid
        self.status = status
        self.side = side
        self.price = price
        self.volume = volume
        self.executed_volume = executed_volume
        self.created = timestamp
        self.modified = timestamp


INSERTION_LOCK = threading.RLock()


def update_order(bot_market_id, refid,
                 status, side, price, volume, executed_volume, timestamp=time.strftime('%Y-%m-%d %H:%M:%S')):

    with INSERTION_LOCK:

        order = SESSION.query(Orders).get(bot_market_id)

        if not order:
            order = Orders(bot_market_id, refid, status, side, price, volume, executed_volume, timestamp)
            SESSION.add(order)
            SESSION.flush()
        else:
            order.status = status
            order.price = price
            order.volume = volume
            order.modified = timestamp
            order.executed_volume = volume
        SESSION.commit()
