import logging
import coloredlogs

root_logger = logging.getLogger(__name__)
root_logger.setLevel(level=logging.DEBUG)
fh = logging.FileHandler('botlib/botlogs/debug.log')
fh.setFormatter(fmt='%(asctime)-20s- %(threadName)-16s - %(levelname)-2s >>> %(message)s')
fh.setLevel(level=logging.DEBUG)
root_logger.addHandler(fh)
coloredlogs.install(level=logging.DEBUG, logger=root_logger, datefmt='%Y-%m-%d %H:%M:%S',
                    fmt='%(asctime)-20s- %(threadName)-16s - %(levelname)-6s >>> %(message)s',
                    milliseconds=True)
