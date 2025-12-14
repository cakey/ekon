"""
Simple Global Agent - Precomputed global prices + cash-adaptive selling

=== EXPERIMENT FINDINGS ===

Iteration 27: Precompute global prices once at round 0.

Key insight: Global price awareness helps, but computing it every round is slow.
Solution: Cache global max prices at round 0 (prices are static).

=== THIS AGENT'S CONFIG ===
- Movement: Random
- Selling: Cash-adaptive threshold (60% poor → 95% rich) relative to global max
- Buying: All profitable items, no filtering

=== PERFORMANCE ===
- $/round:    +$2,011
- ms/round:   0.0029ms
- Efficiency: 689,137

Dominates simple_random and zen_8 on Pareto frontier.
"""

import random


def agent(ws, state, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    meta = ws['meta']
    my_node = world[pos]
    my_shop = my_node['resources']

    # Precompute global prices once at round 0
    if 'global_buy' not in state:
        global_buy = {}
        for node in world.values():
            for res, info in node['resources'].items():
                if info['buy'] > global_buy.get(res, 0):
                    global_buy[res] = info['buy']
        state['global_buy'] = global_buy

    global_buy = state['global_buy']

    # Last round: sell everything
    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': {}, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Random movement
    next_pos = random.choice(neighbors)
    next_shop = world[next_pos]['resources']

    # Cash-adaptive sell threshold
    if coin < 500:
        sell_thresh = 0.60
    elif coin > 10000:
        sell_thresh = 0.95
    else:
        sell_thresh = 0.60 + 0.35 * (coin - 500) / 9500

    # Sell at threshold+ of global max
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            if local_price / gmax >= sell_thresh:
                sells[res] = qty
                coin += qty * local_price

    # Buy anything profitable, prioritize by ratio
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                ratio = next_info['buy'] / price
                trades.append((ratio, res, price, qty))

    trades.sort(reverse=True)
    buys = {}
    budget = coin
    for ratio, res, price, qty in trades:
        if budget <= 0:
            break
        amt = min(budget / price, qty)
        if amt > 0:
            buys[res] = amt
            budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': next_pos
    }
