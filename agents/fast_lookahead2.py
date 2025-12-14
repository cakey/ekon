"""
Fast Lookahead 2 - Two-step arbitrage with efficiency optimization.

Strategy: Look at neighbors AND neighbors-of-neighbors for better trades.
- Find best 2-hop path for arbitrage
- Buy here, sell there in 1-2 steps
"""

import random
from . import utils as u


def find_best_opportunity(world, pos, my_shop):
    """Find best 1 or 2 step arbitrage opportunity."""
    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return None, [], random.choice(list(world.keys()))

    best_profit = 0
    best_trades = []
    best_dest = random.choice(neighbors)
    best_steps = 1

    # Check 1-step opportunities (immediate neighbors)
    for n1 in neighbors:
        n1_shop = world[n1]['resources']
        profit = 0
        trades = []

        for res, info in my_shop.items():
            if info['quantity'] <= 0 or info['sell'] <= 0:
                continue
            if res in n1_shop:
                buy_here = info['sell']
                sell_there = n1_shop[res]['buy']
                if sell_there > buy_here:
                    margin = sell_there - buy_here
                    ratio = sell_there / buy_here
                    profit += margin * info['quantity']
                    trades.append((res, buy_here, info['quantity'], ratio))

        if profit > best_profit:
            best_profit = profit
            best_trades = trades
            best_dest = n1
            best_steps = 1

    # Check 2-step opportunities (neighbors of neighbors) - sample for speed
    for n1 in neighbors[:3]:  # Limit to 3 first-hop neighbors
        n1_neighbors = list(world[n1]['neighbours'].keys())
        for n2 in n1_neighbors[:3]:  # Limit to 3 second-hop neighbors
            if n2 == pos:
                continue
            n2_shop = world[n2]['resources']
            profit = 0
            trades = []

            for res, info in my_shop.items():
                if info['quantity'] <= 0 or info['sell'] <= 0:
                    continue
                if res in n2_shop:
                    buy_here = info['sell']
                    sell_there = n2_shop[res]['buy']
                    if sell_there > buy_here:
                        margin = sell_there - buy_here
                        ratio = sell_there / buy_here
                        # Discount 2-step profit slightly (takes longer)
                        profit += margin * info['quantity'] * 0.8
                        trades.append((res, buy_here, info['quantity'], ratio))

            if profit > best_profit:
                best_profit = profit
                best_trades = trades
                best_dest = n1  # Move toward n2 via n1
                best_steps = 2

    return best_profit, best_trades, best_dest


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

    best_profit, best_trades, best_dest = find_best_opportunity(world, pos, my_shop)

    # Sell everything we're holding
    sells = {r: q for r, q in my_resources.items() if r in my_shop and q > 0}
    for r in sells:
        coin += sells[r] * my_shop[r]['buy']

    # Buy resources sorted by profit ratio
    buys = {}
    best_trades.sort(key=lambda x: x[3], reverse=True)

    for res, price, available, ratio in best_trades:
        if coin <= 0:
            break
        max_qty = coin / price
        qty = min(max_qty, available)
        if qty > 0:
            buys[res] = qty
            coin -= qty * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_dest
    }
