import logging
import sys


formatter = logging.Formatter(fmt='%(asctime)-20s %(threadName)-14s - %(levelname)-5s - %(name)-6s - %(message)s',
                              datefmt='%Y-%m-%d %H:%M:%S')


fh_debug = logging.FileHandler(filename='botlib/data_logs/debug.log')
fh_error = logging.FileHandler(filename='botlib/data_logs/error.log')
fh_trade = logging.FileHandler(filename='botlib/data_logs/trade_options.log')
fh_debug.setLevel(level=logging.DEBUG)
fh_error.setLevel(level=logging.ERROR)
fh_trade.setLevel(level=logging.DEBUG)

fh_debug.setFormatter(fmt=formatter)
fh_error.setFormatter(fmt=formatter)
fh_trade.setFormatter(fmt=formatter)

daemon_logger = logging.getLogger('SYNC')
daemon_logger.addHandler(fh_debug)
daemon_logger.addHandler(fh_error)
daemon_logger.setLevel(level=logging.DEBUG)

api_logger = logging.getLogger('API')
api_logger.addHandler(fh_debug)
api_logger.addHandler(fh_error)
daemon_logger.setLevel(level=logging.DEBUG)
