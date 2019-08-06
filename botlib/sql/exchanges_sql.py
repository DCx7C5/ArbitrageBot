from sqlalchemy import Column, UnicodeText, Integer

from botlib.sql import BASE, SESSION


class Exchanges(BASE):

    __tablename__ = "exchanges"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    active = Column(Integer, default=0)
    key = Column(UnicodeText)
    secret = Column(UnicodeText)

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


Exchanges.__table__.create(checkfirst=True)


def get_exchanges_list():
    try:
        return [x.to_dict() for x in SESSION.query(Exchanges).all()]
    finally:
        SESSION.close()


def count_active_exchanges():
    try:
        return SESSION.query(Exchanges).filter(Exchanges.active == 1).count()
    finally:
        SESSION.close()
