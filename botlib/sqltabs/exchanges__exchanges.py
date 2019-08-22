import threading

from botlib.sqltabs import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR, DATETIME


class Exchanges(BASE):

    __tablename__ = "exchanges__exchanges"
    id = Column(INTEGER(11), primary_key=True)
    cp_refid = Column(VARCHAR(255))
    enabled = Column(TINYINT(1))
    title = Column(VARCHAR(255))
    api_component_name = Column(VARCHAR(255))
    min_order_volume_btc = Column(VARCHAR(255))
    taker_fee = Column(VARCHAR(255))
    maker_fee = Column(VARCHAR(255))
    created = Column(DATETIME)
    modified = Column(DATETIME)

    def __init__(self, cp_refid, enabled, min_profit, title, api_component_name, min_order_volume_btc,
                 taker_fee, maker_fee, created, modified):
        self.cp_refid = cp_refid
        self.enabled = enabled
        self.min_profit = min_profit
        self.title = title
        self.api_component_name = api_component_name
        self.min_order_volume_btc = min_order_volume_btc
        self.taker_fee = taker_fee
        self.maker_fee = maker_fee
        self.created = created
        self.modified = modified


EXCHANGES_INSERTION_LOCK = threading.RLock()
