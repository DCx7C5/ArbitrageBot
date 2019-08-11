import sys
import asyncio
import logging
import threading
from queue import Queue
from random import randint

from botlib.exchanges.agraviex import GraviexClientAIO
from botlib.exchanges.crex import CrexClient

from botlib.sql.aiosql import initialize_mysql_connection, get_bot_markets_table, get_exchanges_table, get_bots_table

formatter = logging.Formatter('%(asctime)-20s- %(threadName)s - %(levelname)-s %(message)s')
formatter.datefmt = '%Y-%m-%d %H:%M:%S'
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
fh = logging.FileHandler(filename='logfile.log')
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logging.basicConfig(level=logging.DEBUG,
                    handlers=[fh, ch],
                    )


class Bot(threading.Thread):

    def __init__(self, bot_id, job_queue):
        threading.Thread.__init__(self)
        self.name = f"WorkerThread-{bot_id}"
        self.daemon = True
        self._exchanges = {}


    async def _run(self):
        while True:
            if
        logging.debug(exchanges)
        bots = await self.initialize_active_bots()
        logging.debug(bots)

    async def initialize_active_bots(self) -> dict:
        prepared = {}
        for x in [i for i in await get_bot_markets_table(self._db_read) if i[3] != 0]:
            if str(x[1]) not in prepared:
                prepared.update({str(x[1]): [(str(x[2]), x[4], x[5], x[6], x[7], x[8])]})
            else:
                prepared[str(x[1])].append((str(x[2]), x[4], x[5], x[6], x[7], x[8]))
        logging.debug('Initialized Active Bot markets ' + str(prepared.keys()))
        return prepared


    def main(self):
        while True:

    def run(self):
        loop = asyncio.get_event_loop()
        loop.set_debug(True)

        try:
            task = loop.create_task(main())
            loop.run_forever()
        except KeyboardInterrupt:
            sys.exit()
        finally:
            loop.run_until_complete(loop.shutdown_asyncgens())


class ArbitrageWorker(threading.Thread):

    def __init__(self, worker_id, job_queue: Queue, main_event_loop):
        threading.Thread.__init__(self)
        self._queue = job_queue
        self._loop = main_event_loop
        self.daemon = True
        self.name = f'WorkerDaemon-{worker_id}'

    async def main(self):
        while True:
            job = self._queue.get()
            if not job:
                await asyncio.sleep(randint(15, 30) / 100)
            if await start_job(job):
                self._queue.task_done()
            await asyncio.sleep(randint(50, 75) / 100)
            self._queue.put()

    async def start_job(self):


    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        task = loop.create_task(self.main())
        loop.run_forever()


class ExchangeManager:

    def __init__(self, exchanges):
        self.exchanges = exchanges


    def get_order_book(self):



class BackGroundIO(threading.Thread):

    def __init__(self):
        threading.Thread.__init__(self)
        self._loop = asyncio.get_event_loop()
        self._request = Queue()
        self._db_read = self.connect_to_database


    async def init_exchanges(self):
        for i in await get_exchanges_table(self._db_read):
            print(i[1])


    @property
    async def connect_to_database(self):
        return await initialize_mysql_connection(self._loop)


    async def task_one(self):
        while True:
            if not self._request:
                await asyncio.sleep(randint(10, 30) / 100)
            else:
                job = self._request.get()


    async def task_two(self):
        while True:
            exchanges = await get_exchanges_table(self._db_read)
            bots = await get_bots_table()
            if self._request:


    def run(self):

        asyncio.set_event_loop(self._loop)
        t1 = self._loop.create_task(self.task_one())

        asyncio.gather(t1, )

async def main():


    await asyncio.sleep(randint(1, 4))

if __name__ == '__main__':
    queue = Queue()
    aqueue = asyncio.Queue()
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    for r in range(5):
        print(r)
        t = Bot(r, queue)
        t.start()

    try:
        task = loop.create_task(main())
        loop.run_forever()
    except KeyboardInterrupt:
        sys.exit()
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
