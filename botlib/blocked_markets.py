import threading
from botlib.bot_log import daemon_logger

# Create child from root logger for OrderBook Daemon
bm_logger = daemon_logger.getChild('BlockedMarkets')


class BlockedMarkets:

    def __init__(self):
        self.__lock = threading.Lock()
        self.__blocked_for_bots = []

    def get_blocked_list(self):
        with self.__lock:
            return self.__blocked_for_bots

    def add_to_blocked_list(self, exchange, refid):
        with self.__lock:
            self.__blocked_for_bots.append((exchange, refid))
        bm_logger.debug(f'Added to blocked markets: {exchange} | {refid}')

    def remove_from_blocked_list(self, exchange, refid):
        with self.__lock:
            self.__blocked_for_bots.remove((exchange, refid))
        bm_logger.debug(f'Removed from blocked markets: {exchange} | {refid}')

    def check_if_in_blocked_list(self, exchange, refid):
        item = (exchange, refid)
        with self.__lock:
            if item in self.__blocked_for_bots:
                return True
            return False
