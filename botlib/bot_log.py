import logging

import coloredlogs

daemon_logger = logging.getLogger('SYNC')

coloredlogs.install(level=logging.DEBUG, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='[%(asctime)-20s] %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                    )
