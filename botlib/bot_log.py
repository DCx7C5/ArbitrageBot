import logging

import coloredlogs

daemon_logger = logging.getLogger('SYNC')
api_logger = logging.getLogger('API')

fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='[%(asctime)]-20s %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

daemon_logger.addHandler(fh)
daemon_logger.setLevel(logging.DEBUG)


coloredlogs.install(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='[%(asctime)-20s] %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                    logger=daemon_logger)
