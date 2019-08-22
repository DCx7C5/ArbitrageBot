from threading import RLock
from botlib.sqltabs import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR, DATETIME


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

    def __init__(self, bot_market_id, refid, status, side, price, volume, executed_volume):
        self.bot_market_id = bot_market_id
        self.refid = refid
        self.status = status
        self.side = side
        self.price = price
        self.volume = volume
        self.executed_volume = executed_volume


ORDER_INSERTION_LOCK = RLock()
