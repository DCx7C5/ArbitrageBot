import ccxt

binance = ccxt.binance()
crex24 = ccxt.crex24()

binance.load_markets()
crex24.load_markets()


for x in binance.markets:
    if x in crex24.markets:
        print("Crex 24 " + x)
