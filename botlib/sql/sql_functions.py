from sqlalchemy import func

from botlib.sql import SESSION
from botlib.sql.arbitrage__bots import Bots
from botlib.sql.exchanges__creds import ExchangesCreds


def get_key_and_secret(exchange) -> tuple:
    try:
        k, s = [(x.to_dict()['api_key'], x.to_dict()['secret']) for x in SESSION.query(ExchangesCreds).filter(
            ExchangesCreds.ex_name == exchange).all()][0]
        return k, s
    finally:
        SESSION.close()


def get_enabled_bots_ids() -> list:
    try:
        return [x[0] for x in SESSION.query(Bots.id).filter(Bots.enabled == 1).all()]
    finally:
        SESSION.close()


def count_enabled_bots() -> int:
    try:
        return SESSION.query(func.count(Bots.id)).filter(Bots.enabled == 1).scalar()
    finally:
        SESSION.close()
