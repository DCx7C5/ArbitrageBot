from threading import RLock

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from botlib.sql import BASE


class Exchanges(BASE):

    __tablename__ = "exchanges"
    id = Column(INTEGER(11), primary_key=True)
    name = Column(VARCHAR(255), nullable=False)
    active = Column(INTEGER(11), default=0)
    key = Column(VARCHAR(255))
    secret = Column(VARCHAR(255))

    def __init__(self, name, active, key, secret):
        self.name = name
        self.active = active
        self.key = key
        self.secret = secret

    def to_dict(self):
        return {
            "name": self.name,
            "active": self.active,
            "key": self.key,
            "secret": self.secret
            }


INSERTION_LOCK = RLock()

