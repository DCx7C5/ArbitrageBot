import time
from queue import Queue
from threading import Lock, Thread

from botlib.bot_log import daemon_logger

# Create child from daemon_logger for Jobs Daemon
od_logger = daemon_logger.getChild('OrderManager')

# Create child from od_logger for Jobs Daemon
aj_logger = od_logger.getChild('Job')


class ArbitrageJob(Thread):

    def __init__(self, job):
        Thread.__init__(self)
        self.__job = job
        self.name = f'ArbitrageJob'

    def do_sell_order(self):
        pass

    def do_buy_order(self):
        pass

    def run(self) -> None:
        pass


class OrderManagerDaemon(Thread):

    def __init__(self, ):
        Thread.__init__(self)
        self.daemon = True
        self.name = 'JobsOrdersSync'
        self.__lock = Lock()
        self.__job_queue = Queue()
        self.__logger = od_logger
        self.__last_log = time.time()

    def add_to_job_queue(self, job):
        with self.__lock:
            self.__job_queue.put(job)

    def run(self) -> None:
        self.__logger.info('Daemon started!')
        while True:
            if self.__job_queue.empty():
                time.sleep(.5)
                continue
            job = self.__job_queue.get()
            ArbitrageJob(job).start()
            if time.time() > self.__last_log + 20:
                self.__logger.debug(f'Waiting for jobs...')
                self.__last_log = time.time()
            time.sleep(.5)
