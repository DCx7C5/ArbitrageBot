

class Storage:
    """
    Own class implementation to support additional dictionary actions on class
    """
    def __getitem__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError:
            return False
        except KeyError:
            return False

    def __getattr__(self, item):
        try:
            return self.__getattribute__(item)
        except AttributeError:
            return False
        except KeyError:
            return False

    def __setitem__(self, key, value):
        return self.__setattr__(key, value)

    def __repr__(self):
        return str(self.__dict__)
