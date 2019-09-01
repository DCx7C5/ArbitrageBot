from botlib.blocked_markets import BlockedMarkets
blocked = BlockedMarkets()


test = [  # Exchange, market, highest_bid, lowest_ask
    ('Graviex', 'ethbtc', [0.006780001, 0.0626], [0.006994, 0.4374]),
    ('Crex24', 'ETH-BTC', [0.00662, 1.14456675], [0.00663, 38.85907479]),
    ('Binance', 'ETHBTC', [0.006635, 7.39], [0.006641, 4.91]),
    ('Test0', 'ETHBTC', [0.006625, 7.39], [0.006631, 4.91]),
    ('Test1', 'ETHBTC', [0.006935, 7.39], [0.007041, 4.91]),

]


def check_min_profit(bids, asks):
    rate = round((bids[2][0] - asks[3][0]) / bids[2][0] * 100, 2)
    if rate >= float(1):
        return rate
    return None


def check_quantity_against_min_order_amount(options):
    for opt in options:
        for side in opt:
            if isinstance(side, list):
                if not float(0) < side[3]:
                    options.remove(opt)
    return options


def define_max_order_size_per_option(options):
    for opt in options:
        for side in opt:
            if isinstance(side, list):
                if side[2] * side[3] < 0.002:
                    order_size_max = round(side[3], 8)
                else:
                    order_size_max = round(0.0002 / side[2], 8)
                side.append(order_size_max)
        possible = min(opt[0][4], opt[1][4])
        opt[0][4] = possible
        opt[1][4] = possible
    return options


def check_balances_per_option(options):
    return options


def calculate_profit_per_option(options):
    for opt in options:
        sell_market = opt[0][4] * opt[0][2]
        buy_market = opt[1][4] * opt[1][2]
        profit = round(float(sell_market - buy_market), 8)
        opt.append(profit)
    return options


def filter_based_on_most_profitable(options):
    _opt = None
    _val = 0
    for opts in options:
        if opts[-1] > _val:
            _opt = opts
            _val = opts[-1]
    blocked.add_to_blocked_list(_opt[0][0], _opt[0][1])
    blocked.add_to_blocked_list(_opt[1][0], _opt[1][1])
    return _opt


jobs = []

options = []

for bids in test:
    for asks in test:
        if bids is not asks:
            rate = check_min_profit(bids, asks)
            if rate is None:
                continue
            options += [[[bids[0], bids[1], bids[2][0], bids[2][1]], [asks[0], asks[1], asks[3][0], asks[3][1]], rate]]


options = check_quantity_against_min_order_amount(options)
options = define_max_order_size_per_option(options)
options = check_balances_per_option(options)
options = calculate_profit_per_option(options)
print(options)
options = filter_based_on_most_profitable(options)
