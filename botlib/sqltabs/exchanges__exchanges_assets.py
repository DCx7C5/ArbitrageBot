import threading

from botlib.sqltabs import BASE
from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR


class ExchangesAssets(BASE):

    __tablename__ = "exchanges__exchanges_assets"
    id = Column(INTEGER(11), primary_key=True)
    exchange_id = Column(VARCHAR(255))
    asset_id = Column(TINYINT(1))
    refid = Column(VARCHAR(255))
    deposit_enabled = Column(VARCHAR(255))
    withdraw_enabled = Column(VARCHAR(255))
    withdraw_fee = Column(VARCHAR(255))

    def __init__(self, exchange_id, asset_id, refid, deposit_enabled, withdraw_enabled, withdraw_fee):
        self.exchange_id = exchange_id
        self.asset_id = asset_id
        self.refid = refid
        self.deposit_enabled = deposit_enabled
        self.withdraw_enabled = withdraw_enabled
        self.withdraw_fee = withdraw_fee


EXAS_INSERTION_LOCK = threading.RLock()
