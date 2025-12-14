"""
Experimental Agent v9 - Zen with blitz optimizations

Testing what makes blitz more profitable than zen_all:
1. Float math (instead of integer division)
2. Random exploration when no profitable trade

Hypothesis: Random exploration finds better positions over 200 rounds.
"""

import random
_r = random.choice


def agent(world_state, *args, **kwargs):
    you = world_state['you']
    pos = you['position']
    coin = you['coin']
    my_res = you['resources']
    world = world_state['world']
    node = world[pos]
    shop = node['resources']

    # Sell everything we have
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in shop:
            sells[res] = qty
            coin += qty * shop[res]['buy']

    neighbors = node['neighbours']
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Check all neighbors, pick best arbitrage (using FLOAT math like blitz)
    best_dest = None
    best_profit = 0
    best_buys = {}

    for n in neighbors:
        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin  # float

        for res, info in shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0 and budget > 0:
                n_info = n_shop.get(res)
                if n_info and n_info['buy'] > price:
                    amt = min(budget / price, qty)  # FLOAT division
                    buys[res] = amt
                    budget -= amt * price
                    profit += (n_info['buy'] - price) * amt

        if profit > best_profit:
            best_profit = profit
            best_dest = n
            best_buys = buys

    # Random exploration when no profitable trade (like blitz)
    if not best_dest:
        nbs = list(neighbors.keys())
        best_dest = _r(nbs) if nbs else pos
        best_buys = {}

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys,
        'move': best_dest
    }
