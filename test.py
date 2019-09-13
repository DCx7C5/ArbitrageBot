import time
from botlib.api_client.api_wrapper import Exchange

clients = Exchange()


def timeit(function):
    def _wrapper(self, *args, **kwargs):
        start = time.time()
        print(f"Starting function: {start}")
        res = function(self, *args, **kwargs)
        end = time.time()
        print(f"Ending function: {end}\nFunction call took {round(end - start, 4)}")
        return res
    return _wrapper


@timeit
def time_some_func(ob_size):
    return clients.get_order_book('Binance', 'DOGEBTC', ob_size)


t = time_some_func(10)
print(t)

t = time_some_func(50)
print(t, len(t))

t = time_some_func(100)
print(t, len(t))
