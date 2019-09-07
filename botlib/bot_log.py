import logging

import coloredlogs

daemon_logger = logging.getLogger('SYNC')
api_logger = logging.getLogger('API')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='[%(asctime)-20s] %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')
fh.setFormatter(formatter)

daemon_logger.addHandler(fh)
daemon_logger.setLevel(logging.DEBUG)


coloredlogs.install(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='[%(asctime)-20s] %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                    logger=daemon_logger)


# Create child from daemon_logger for Jobs Daemon
od_logger = daemon_logger.getChild('OrderManager')

# Create child from od_logger for Jobs Daemon
aj_logger = od_logger.getChild('Job')

# Create child from root logger for OrderBook Daemon
ob_logger = daemon_logger.getChild('OrderBook')

# Create child from or-bo daemon for 'FireAndForget-Threads'
req_logger = od_logger.getChild('Req')

arbi_logger = daemon_logger.getChild('Arbitrage')

