import threading

from sqlalchemy import Column, UnicodeText, Integer, Float

from botlib.sql import BASE, SESSION


class Coins(BASE):

    __tablename__ = "coins"
    id = Column(Integer, primary_key=True)
    name = Column(UnicodeText, nullable=False)
    active = Column(Integer, default=0)
    min_amount = Column(Float)
    max_amount = Column(Float)
    order_book_length = Column(Integer, default=25)

    def __init__(self, name, active, min_amount=None, max_amount=None, order_book_length=None):
        self.name = name
        self.active = active
        self.min_amount = min_amount
        self.max_amount = max_amount
        self.order_book_length = order_book_length

    def to_dict(self):
        return {
            "name": self.name,
            "active": self.active,
            "min": self.min_amount,
            "max": self.max_amount,
            "ob_length": self.order_book_length
            }


Coins.__table__.create(checkfirst=True)
MARKETS_INSERTION_LOCK = threading.RLock()


def get_coins_list():
    try:
        return [x.to_dict() for x in SESSION.query(Coins).all()]
    finally:
        SESSION.close()


def get_active_coins_list():
    try:
        return [x.to_dict() for x in SESSION.query(Coins).filter(Coins.active == 1).all()]
    finally:
        SESSION.close()


def get_order_book_length(coin):
    try:
        return SESSION.query(Coins.order_book_length).filter(Coins.name == coin).all()[0]
    finally:
        SESSION.close()


def deactivate_coin(coin):
    with MARKETS_INSERTION_LOCK:
        coin = SESSION.query(Coins).get(coin)

        if not coin:
            coin = Coins(coin, 0)
            SESSION.add(coin)
            SESSION.flush()
        else:
            coin.active = 0

        SESSION.commit()


def activate_coin(coin):
    with MARKETS_INSERTION_LOCK:
        coin = SESSION.query(Coins).get(coin)

        if not coin:
            coin = Coins(coin, 1)
            SESSION.add(coin)
            SESSION.flush()
        else:
            coin.active = 1

        SESSION.commit()
