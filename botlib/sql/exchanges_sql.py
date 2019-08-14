import threading

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from botlib.sql import BASE, SESSION


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


INSERTION_LOCK = threading.RLock()


def get_exchanges_sql(name=None, active=False):
    try:
        if active:
            return [x.to_dict() for x in SESSION.query(Exchanges).filter(Exchanges.active == 1).all()]
        return [x.to_dict() for x in SESSION.query(Exchanges).all()]
    finally:
        SESSION.close()


def get_key_and_secret(exchange):
    try:
        k, s = [(x.to_dict()['key'], x.to_dict()['secret']) for x in SESSION.query(Exchanges).filter(Exchanges.name == exchange).all()][0]
        return k, s
    finally:
        SESSION.close()
