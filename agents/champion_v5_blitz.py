"""
Champion Agent v5 (Blitz variant) - Blitz + Neighbor-Aware Selling

=== EXPERIMENT FINDINGS (Iteration 5) ===

Tested neighbor-aware selling across all frontier agents.
Blitz + NAS improves blitz by +$212/round with no time cost.

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 1 (same as blitz)
- Neighbor-aware selling: only sell if destination doesn't pay more
- No global price computation

=== PERFORMANCE ===
- $/round:    +$3,748
- ms/round:   0.007ms
- Efficiency: 535,429 ($/round/ms)

Replaces blitz on the Pareto frontier.
"""

import random
_r = random.choice


def agent(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_shop = world[pos]['resources']
    meta = ws['meta']

    # Last round - sell everything
    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Find best neighbor (same as blitz)
    best_n = pos
    best_profit = 0
    best_buys = None

    for n in neighbors:
        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin

        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0 and budget > 0:
                n_info = n_shop.get(res)
                if n_info and n_info['buy'] > price:
                    amt = min(budget / price, qty)
                    buys[res] = amt
                    budget -= amt * price
                    profit += (n_info['buy'] - price) * amt

        if profit > best_profit:
            best_profit = profit
            best_n = n
            best_buys = buys

    if not best_buys:
        best_n = _r(neighbors) if neighbors else pos

    # Neighbor-aware selling: only sell if destination doesn't pay more
    dest_shop = world[best_n]['resources']
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            current_price = my_shop[res]['buy']
            dest_info = dest_shop.get(res)
            dest_price = dest_info['buy'] if dest_info else 0
            if current_price >= dest_price:
                sells[res] = qty

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys or {},
        'move': best_n
    }
