from sqlalchemy import Column
from sqlalchemy.dialects.mysql import INTEGER, VARCHAR

from botlib.sql import BASE


class ExchangesCreds(BASE):

    __tablename__ = "exchanges__creds"
    id = Column(INTEGER(11), primary_key=True)
    ex_name = Column(VARCHAR(255))
    api_key = Column(VARCHAR(255))
    secret = Column(VARCHAR(255))

    def __init__(self, name, key, secret):
        self.ex_name = name
        self.api_key = key
        self.secret = secret

    def to_dict(self):
        return {
            "name": self.ex_name,
            "api_key": self.api_key,
            "secret": self.secret
            }
