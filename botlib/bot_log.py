import logging

import coloredlogs

root_logger = logging.getLogger('Bot')
fh = logging.FileHandler('debug.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter(fmt='%(asctime)-20s %(name)-14s %(threadName)-14s - %(levelname)-7s - %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')

root_logger.addHandler(fh)
root_logger.setLevel(logging.DEBUG)

coloredlogs.install(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='%(asctime)-20s %(name)-14s %(threadName)-14s - %(levelname)-7s - %(message)s',
                    logger=root_logger
                    )
