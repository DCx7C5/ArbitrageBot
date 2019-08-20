from threading import Thread


class ArbitrageBot(Thread):

    def __init__(self, bot_id: int, order_books: dict):
        super().__init__()
        self.bot_id = bot_id
        self.name = f"BotID {self.bot_id} | Arbitrage"

        self._order_books = order_books
        self._options = []

    def get_arbitrage_options(self):
        for e
        # Get highest bid / volume
        self._hbe = max(self._data, key=lambda x: float(self._data.get(x)[0][0][0]))
        self._hbn = float(self._data.get(self._hbe)[0][0][0])

        # Get lowest ask / volume
        self._lae = min(self._data, key=lambda x: float(self._data.get(x)[1][0][0]))
        self._lan = float(self._data.get(self._lae)[1][0][0])

        # Check spread rate
        if round((self._hbn - self._lan) / self._hbn * 100, 2) < 1:
            return False

        # Prevent other threads to start jobs with same bot_id
        c_lock.add_to_locker(self.bot_id)

        # Check Order Volume
        self._hbv = float(self._data.get(self._hbe)[0][0][1])
        self._lav = float(self._data.get(self._lae)[1][0][1])

        # Check that values not exceeding any limits (profit ra)
        if not (self.ex[self._hbe]['min_size'] > self._hbv < self.ex[self._hbe]['max_size']):
            return False
        if not (self.ex[self._lae]['min_size'] > self._lav < self.ex[self._lae]['max_size']):
            return False

        # Check against own coin balance (sell) and btc (buy)
        bal_c = self.ex[self._hbe]

        return True

    def fetch_order_books(self):
        self._data = {}
        for mkt in bot_markets_from_bot_id(self.bot_id):
            self._data.update({mkt[0]: self.ex.get_order_book(mkt[0], mkt[1])})
        self.arbitrage_check()
        return True

    def run(self) -> None:
        if self.fetch_order_books():
            pass
        if self.arbitrage_check():
            pass

        del self
        return

