from threading import RLock

from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR

from botlib.sql import BASE, SESSION


class Bots(BASE):

    __tablename__ = "bots"
    id = Column(INTEGER(11), primary_key=True)
    title = Column(VARCHAR(255))
    enabled = Column(TINYINT(1))

    def __init__(self, title, enabled):
        self.title = title
        self.enabled = enabled

    def to_dict(self):
        return {
            "title": self.title,
            "enabled": self.enabled
            }


Bots.__table__.create(checkfirst=True)
BOTS_INSERTION_LOCK = RLock()


def update_bots(title, enabled=0):
    with BOTS_INSERTION_LOCK:

        bot = SESSION.query(Bots).get(title)

        if not bot:
            bot = Bots(title, enabled)
            SESSION.add(bot)
            SESSION.flush()
        else:
            bot.enabled = enabled
        SESSION.commit()
