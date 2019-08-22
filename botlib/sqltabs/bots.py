from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, TINYINT, VARCHAR

from botlib.sqltabs import BASE


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
            "id": self.id,
            "title": self.title,
            "enabled": self.enabled
            }

