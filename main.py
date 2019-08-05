import sys
import logging
import threading
from botlib.graviex import GraviexClient
from config.configmanager import ExchConfManager

logging.basicConfig(level=logging.DEBUG,
                    format='[%(levelname)s] (%(threadName)-10s) %(message)s',
                    )

EXCHANGES = {}
TICKERS = {}
ORDERBOOKS = {}

e_lock = threading.RLock()
t_lock = threading.RLock()
o_lock = threading.RLock()


class Exchanges:

    def __init__(self):
        self.clients = {}
        self.c_lock = threading.RLock()
        self.cfg_man = ExchConfManager()
        self._exchange_configs = self.cfg_man.get_active_exchanges()

        # get active exchs on init
        self.init_active_exchanges()

    def init_active_exchanges(self):
        with self.c_lock:
            for i in self._exchange_configs:
                if i in self.clients.keys():
                    continue
                if i == "graviex":
                    exch = GraviexClient(
                        api_key=self._exchange_configs['graviex'].get('api_key'),
                        api_secret=self._exchange_configs['graviex'].get('api_secret')
                    )

                    self.clients.update({i: exch})

    def get_clients(self):
        with self.c_lock:
            return self.clients




class ArbitrageBot:

    def __init__(self):
        self.exchs = {}
        self.tickers = {}
        self.orderbook = {}


    def start(self):
        tickerdaemon = TickersDaemon()
        tickerdaemon.start()


if __name__ == '__main__':
    bot = Exchanges()
    bot.init_active_exchanges()
    try:
        bot.init_active_exchanges()
    except KeyboardInterrupt:
        sys.exit()
