import os
import logging

CWD = os.getcwd()

formatter = logging.Formatter('%(asctime)-20s- %(threadName)s - %(levelname)-s >>> %(message)s')
formatter.datefmt = '%Y-%m-%d %H:%M:%S'
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
ch.setFormatter(formatter)
fh = logging.FileHandler(filename=f"{CWD}/logfile.log",)
fh.setLevel(logging.DEBUG)
fh.setFormatter(formatter)
logging.basicConfig(level=logging.INFO,
                    handlers=[fh, ch],
                    )

logger = logging.getLogger(__name__)
logger.addHandler(ch)
logger.addHandler(fh)
