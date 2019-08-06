import threading

from sqlalchemy import Column, UnicodeText, Integer, Time, TIMESTAMP

from botlib.sql import BASE, SESSION


class PlacedOrders(BASE):

    __tablename__ = "placed_orders"
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, nullable=False)
    market = Column(UnicodeText, nullable=False)
    order_type = Column(UnicodeText, nullable=False)
    exchange = Column(UnicodeText, nullable=False)
    status = Column(UnicodeText, nullable=False)

    def __init__(self, order_id, market, order_type, exchange, status):
        self.order_id = order_id
        self.market = market
        self.order_type = order_type
        self.exchange = exchange
        self.status = status

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "market": self.market,
            "order_type": self.order_type,
            "exchange": self.exchange,
            "status": self.status,
            }


PlacedOrders.__table__.create(checkfirst=True)
ORDER_INSERTION_LOCK = threading.RLock()


def update_order(order_id, market, order_type, exchange, status):
    with ORDER_INSERTION_LOCK:

        order = SESSION.query(PlacedOrders).get(order_id)

        if not order:
            order = PlacedOrders(order_id, market, order_type, exchange, status)
            SESSION.add(order)
            SESSION.flush()
        else:
            order.status = status

        SESSION.commit()


def get_order_by_id(order_id):
    try:
        return SESSION.query(PlacedOrders).get(PlacedOrders.order_id == int(order_id)).first()
    finally:
        SESSION.close()
