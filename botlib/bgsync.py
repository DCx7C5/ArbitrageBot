import time
from threading import RLock, Thread

from botlib.sql.sql_functions import get_enabled_bots_ids, get_active_bot_markets_sql
from botlib.storage import Storage


class BackGroundDaemon(Thread, Storage):

    def __init__(self):
        Thread.__init__(self)
        self.name = 'BackGroundSync'
        self.daemon = True
        self.__lock = RLock()

        # List of enabled bot ids
        self.enabled_bot_ids = []

        # List of locked bot ids
        self.locked_bot_ids = []

        # List with tuples (bot_id, exchange, refid)
        self.bot_markets = []

        self.start()

    def __update_enabled_bot_ids(self, bot_ids: list):
        for bid in bot_ids:
            if bid not in self.enabled_bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.append(bid)
                print(f"ADDED Bot ID {bid} TO self.__enabled_bot_ids")
        for bid in self.enabled_bot_ids:
            if bid not in bot_ids:
                with self.__lock:
                    self.enabled_bot_ids.remove(bid)
                    self.remove_from_locked_bot_ids(bid)
                print(f"REMOVED Bot ID {bid} FROM self.__enabled_bot_ids")

    def remove_from_locked_bot_ids(self, bot_id: int):
        if not self.locked_bot_ids:
            return
        with self._lock:
            self.locked_bot_ids.remove(bot_id)

    def add_to_locked_bot_ids(self, bot_id: int):
        with self.__lock:
            self.locked_bot_ids.append(bot_id)

    def get_bot_markets(self):
        with self.__lock:
            return self.bot_markets

    def count_enabled_bot_ids(self):
        with self.lock:
            return len(self.enabled_bot_ids)

    def run(self):
        while True:
            ids = get_enabled_bots_ids()
            self.__update_enabled_bot_ids(ids)
            with self.__lock:
                self.bot_markets = get_active_bot_markets_sql(ids)
            time.sleep(1.5)
