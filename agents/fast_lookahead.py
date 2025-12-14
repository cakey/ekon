"""
Fast Lookahead Agent - Optimized for efficiency ($/round/ms)

Strategy: 1-step arbitrage like pirate, but cleaner implementation.
- Find neighbor with best profit opportunity
- Buy resources here that sell for more at that neighbor
- Sort by profit RATIO (not absolute margin) for better ROI
"""

import random
from . import utils as u


def agent(world_state, *args, **kwargs):
    pos = world_state['you']['position']
    coin = world_state['you']['coin']
    my_resources = world_state['you']['resources']
    world = world_state['world']
    my_shop = world[pos]['resources']

    # Last round - sell everything
    if u.is_last_round(world_state):
        sells = {r: q for r, q in my_resources.items() if r in my_shop and q > 0}
        return {
            'resources_to_sell_to_shop': sells,
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(world[pos]['neighbours'].keys())

    # Find best neighbor by potential profit
    best_neighbor = random.choice(neighbors) if neighbors else pos
    best_profit = 0
    best_trades = []  # (resource, buy_price, quantity, ratio)

    for neighbor in neighbors:
        neighbor_shop = world[neighbor]['resources']
        profit = 0
        trades = []

        for res, info in my_shop.items():
            if info['quantity'] <= 0 or info['sell'] <= 0:
                continue
            if res in neighbor_shop:
                buy_here = info['sell']
                sell_there = neighbor_shop[res]['buy']
                if sell_there > buy_here:
                    margin = sell_there - buy_here
                    ratio = sell_there / buy_here  # ROI ratio
                    profit += margin * info['quantity']
                    trades.append((res, buy_here, info['quantity'], ratio))

        if profit > best_profit:
            best_profit = profit
            best_neighbor = neighbor
            best_trades = trades

    # Sell everything we're holding (we bought it to sell here)
    sells = {r: q for r, q in my_resources.items() if r in my_shop and q > 0}
    for r in sells:
        coin += sells[r] * my_shop[r]['buy']

    # Buy resources sorted by profit ratio (best ROI first)
    buys = {}
    best_trades.sort(key=lambda x: x[3], reverse=True)

    for res, price, available, ratio in best_trades:
        if coin <= 0:
            break
        max_qty = coin / price  # sim.py will truncate to int
        qty = min(max_qty, available)
        if qty > 0:
            buys[res] = qty
            coin -= qty * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_neighbor
    }
