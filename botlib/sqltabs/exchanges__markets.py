import threading

from botlib.sqltabs import BASE
from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.mysql import INTEGER, DECIMAL, VARCHAR, DATETIME


class ExchangesMarkets(BASE):

    __tablename__ = "exchanges__markets"
    id = Column(INTEGER(11), primary_key=True)
    exchange_id = Column(INTEGER(11), ForeignKey('exchanges__exchanges.id'))
    base_exchange_asset_id = Column(INTEGER(11))
    quote_exchange_asset_id = Column(INTEGER(11))
    refid = Column(VARCHAR(255))
    title = Column(VARCHAR(255))
    last_price = Column(VARCHAR(255))
    price_change = Column(VARCHAR(255))
    bid = Column(VARCHAR(255))
    ask = Column(VARCHAR(255))
    volume_24h = Column(VARCHAR(255))
    quote_volume = Column(VARCHAR(255))
    decimals = Column(VARCHAR(255))
    min_step = Column(VARCHAR(255))
    withdrawal_fee = Column(DECIMAL(6, 4))
    updated_ts = Column(INTEGER(32))
    created = Column(DATETIME)
    modified = Column(DATETIME)


EXMA_INSERTION_LOCK = threading.RLock()
