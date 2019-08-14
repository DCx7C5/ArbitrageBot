import threading
import time
from random import randint


from botlib.sql.bot_markets_sql import get_bot_market_sql


class BackgroundLogger(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.name = "BackGroundDaemon"
        self.bot_markets = []
        self._bm_lock = threading.RLock()
        self._quit_flag = False

    def synchronize_database(self):
        time.sleep(randint(30, 80) / 100)
        for abm in get_bot_market_sql():
            if abm not in self.bot_markets:
                with self._bm_lock:
                    self.bot_markets.append(abm)

    def quit(self):
        self._quit_flag = True
        del self

    def run(self) -> None:
        while not self._quit_flag:
            self.synchronize_database()
