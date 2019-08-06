from threading import RLock, Thread, Event

from secrets import SystemRandom
from botlib.crex import CrexClient
from botlib.graviex import GraviexClient

from botlib.sql.coins_sql import get_coins_list
from botlib.sql.exchanges_sql import get_exchanges_list

sec = SystemRandom()

ACTIVE_COINS = {}
EXCHANGES = {}

COINS_LOCK = RLock()
EXCHANGE_LOCK = RLock()



def update_active_exchanges():
    for i in get_exchanges_list():
        with EXCHANGE_LOCK:
            if i['active'] == 1 and i['name'] not in EXCHANGES.keys():
                if i['name'] == 'graviex':
                    EXCHANGES.update({i['name']: GraviexClient(i['key'], i['secret'])})
                elif i['name'] == 'crex':
                    EXCHANGES.update({i['name']: CrexClient(i['key'], i['secret'])})
            if i['active'] == 0 and i['name'] in EXCHANGES.keys():
                del EXCHANGES[i['name']]
    return True


def get_exchanges(exchange=None):
    with EXCHANGE_LOCK:
        if exchange:
            return EXCHANGES[exchange]
        return EXCHANGES


def get_coins(coin=None):
    with COINS_LOCK:
        if coin:
            return ACTIVE_COINS[coin]
        return ACTIVE_COINS


def count_exchanges():
    with EXCHANGE_LOCK:
        return len(EXCHANGES.keys())


def update_active_coins():
    for i in get_coins_list():
        with COINS_LOCK:
            if i['active'] == 1 and i['name'] not in ACTIVE_COINS.keys():
                ACTIVE_COINS.update({
                    i['name']: {
                         'active': i['active'],
                         'min_amount': i['min'],
                         'max_amount': i['max'],
                         'ob_length': i['ob_length']
                         }
                }
                )
            if i['active'] == 0 and i['name'] in ACTIVE_COINS.keys():
                del ACTIVE_COINS[i['name']]
    return True


def count_coins(coin_dict, coin_lock):
    with coin_lock:
        return len(coin_dict.keys())


class DatabaseThread(Thread):

    def __init__(self, api_update_event: Event, coin_update_event: Event):
        Thread.__init__(self)
        self.name = f'Database.Thread'
        self.timer = Event()
        self.api_update_event = api_update_event
        self.coin_update_event = coin_update_event

    def run(self):
        while True:
            if update_active_exchanges():
                self.api_update_event.set()
            print(get_exchanges().keys())
            self.timer.wait(sec.randint(6, 16) / 10)

            if update_active_coins():
                self.coin_update_event.set()
            print(get_coins().keys())
            self.timer.wait(sec.randint(6, 16) / 10)
