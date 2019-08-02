import asyncio
import logging


class ArbitrageBot:

    def __init__(self, debug=False):
        self.main_loop = asyncio.new_event_loop()
        self.active_exchanges = list()

        if debug is True:
            self.main_loop.set_debug(True)

        logging.basicConfig(
            level=logging.DEBUG if debug else logging.INFO
        )

    async def main(self):
        while True:
            await asyncio.sleep(1)
            print("sleep")

    async def initialize2_exchange(self):
        while True:
            await asyncio.sleep(1.5)
            return print("sleep2")

    def start(self):
        asyncio.gather(self.main(), self.initialize2_exchange())
        self.main_loop.run_forever()

    def quit(self):
        self.main_loop.close()


if __name__ == '__main__':
    bot = ArbitrageBot()
    try:
        bot.start()
    except KeyboardInterrupt:
        bot.quit()
