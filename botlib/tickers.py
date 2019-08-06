import threading

from botlib.exchanges import get_exchanges


class UpdateTickers(threading.Thread):

    def __init__(self, event: threading.Event):
        threading.Thread.__init__(self)
        self.name = f"Update-Tickers-Daemon"



