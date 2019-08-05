from sqlalchemy import Column, UnicodeText, Integer

from botlib.sql import BASE, SESSION


class Coins(BASE):

    __tablename__ = "coins"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    active = Column(Integer, default=0)

    def __init__(self, id, name, active):
        self.id = id
        self.name = name
        self.active = active

    def to_dict(self):
        return {
            "name": self.name,
            "active": self.active
            }


Coins.__table__.create(checkfirst=True)


def get_coins_list():
    try:
        return [x.to_dict() for x in SESSION.query(Coins).all()]
    finally:
        SESSION.close()
