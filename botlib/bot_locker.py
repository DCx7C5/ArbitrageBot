from threading import RLock

from botlib.storage import Storage


class BotLocker(Storage):

    def __init__(self):
        self.__lock = RLock()
        self.__locked_bot_ids = []

    def lock_bot_id(self, bot_id):
        with self.__lock:
            self.__locked_bot_ids.append(bot_id)

    def remove_lock(self, bot_id):
        with self.__lock:
            self.__locked_bot_ids.remove(bot_id)
