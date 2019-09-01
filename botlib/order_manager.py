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
        self.daemon = True
        self.name = 'JobsOrdersSync'
        self.__lock = Lock()
        self.__job_queue = Queue()
        self.__logger = od_logger
        self.__last_log = time.time()

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            if self.__job_queue.empty():
                time.sleep(.5)
                continue
            args = self.__job_queue.get()
            if time.time() > self.__last_log + 20:
                self.__logger.debug(f'Waiting for orders...')
                self.__last_log = time.time()
            time.sleep(.25)