import threading


class SettingsCache:

    def __init__(self):
        self.__lock = threading.Lock()