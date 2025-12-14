"""
Ultrafast Agent - Maximum efficiency through minimal computation.

Strategy: Find best neighbor, buy all profitable items there.
"""

import random

_rng = random.randint


def agent(world_state, *args, **kwargs):
    you = world_state['you']
    pos = you['position']
    coin = you['coin']
    world = world_state['world']
    current = world[pos]
    my_shop = current['resources']

    # Last round - sell everything
    if world_state['meta']['current_round'] == world_state['meta']['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in you['resources'].items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    # Sell everything
    sells = {r: q for r, q in you['resources'].items() if q > 0 and r in my_shop}
    for r, q in sells.items():
        coin += q * my_shop[r]['buy']

    neighbors = current['neighbours']
    neighbor_keys = list(neighbors.keys())
    n_count = len(neighbor_keys)

    # Find best neighbor by total profit, track all trades
    best_n = None
    best_profit = 0
    best_trades = None

    for i in range(n_count):
        n = neighbor_keys[i]
        n_shop = world[n]['resources']
        profit = 0
        trades = []

        for res, info in my_shop.items():
            qty = info['quantity']
            price = info['sell']
            if qty > 0 and price > 0:
                n_info = n_shop.get(res)
                if n_info:
                    buy = n_info['buy']
                    if buy > price:
                        margin = buy - price
                        profit += margin * qty
                        trades.append((res, price, qty, buy / price))

        if profit > best_profit:
            best_profit = profit
            best_n = n
            best_trades = trades

    # Buy all profitable trades at best neighbor
    if best_n and best_trades:
        best_trades.sort(key=lambda x: x[3], reverse=True)
        buys = {}
        for res, price, qty, _ in best_trades:
            if coin <= 0:
                break
            amt = min(coin / price, qty)
            if amt > 0:
                buys[res] = amt
                coin -= amt * price
        return {
            'resources_to_sell_to_shop': sells,
            'resources_to_buy_from_shop': buys,
            'move': best_n
        }

    # Random exploration
    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': {},
        'move': neighbor_keys[_rng(0, n_count - 1)] if n_count else pos
    }
