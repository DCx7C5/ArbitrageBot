import random
import time
from queue import Queue
from threading import Lock, Thread
from collections import Counter

from botlib.bot_log import daemon_logger

# Create child from root logger for OrderBook Daemon
od_logger = daemon_logger.getChild('OrderManager')


class CreateOrder(Thread):

    def __init__(self):
        Thread.__init__(self)



class OrderManagerDaemon(Thread):

    def __init__(self):
        Thread.__init__(self)
        self.__lock = Lock()
        self.__job_queue = Queue()


    def run(self) -> None:
        self._logger.info('Daemon started!')
        while True:
            if self.__job_queue.empty():
                self.__fill_queue()
            args = self.queue.get()
            if not self._order_book_timer.check_bot_market_last_call(args[1], args[2]):
                self.queue.task_done()
                continue
            else:
                if time.time() > self._last_log + 20:
                    self._logger.debug(f'Exchanges syncing to bot... Sub-threads active:{self.__count_sub_threads()}')
                    self._last_log = time.time()
            time.sleep(.25)