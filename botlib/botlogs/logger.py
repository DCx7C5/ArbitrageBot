import logging
import coloredlogs

root_logger = logging.getLogger(__name__)
fh = logging.FileHandler('botlib/botlogs/debug.log')

root_logger.addHandler(fh)

coloredlogs.install(level=logging.INFO, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='[%(asctime)-20s-] %(threadName)-16s - %(levelname)-6s >>> %(message)s',
                    milliseconds=True)
