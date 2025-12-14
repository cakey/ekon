"""
Global Arbitrage Plus - Global arb + 1-node profit with leftover cash

=== EXPERIMENT FINDINGS ===

Iteration 30: Combine global arbitrage with 1-node profit opportunities.

Strategy:
1. Global arb buys first (buy cheap relative to global)
2. With leftover cash, buy items profitable at next neighbor

Cash-adaptive thresholds:
- Poor ($<500): buy at <=80% of global, sell at >=70% of global
- Rich ($>10000): buy at <=75% of global, sell at >=85% of global

=== PERFORMANCE ===
- $/round:    +$4,230
- ms/round:   0.0035ms
- Efficiency: 1,203,340

On frontier between global_arb ($3,988 @ 0.0028ms) and depth2_top2_nas ($4,911 @ 0.029ms)
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

    # Precompute global prices once
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

    # Cash-adaptive thresholds
    if coin < 500:
        buy_thresh = 0.80
        sell_thresh = 0.70
    elif coin > 10000:
        buy_thresh = 0.75
        sell_thresh = 0.85
    else:
        t = (coin - 500) / 9500
        buy_thresh = 0.80 + (0.75 - 0.80) * t   # 80% -> 75%
        sell_thresh = 0.70 + (0.85 - 0.70) * t  # 70% -> 85%

    # SELL at expensive nodes
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            if local_price / gmax >= sell_thresh:
                sells[res] = qty
                coin += qty * local_price

    buys = {}
    budget = coin

    # PHASE 1: Global arb buys (cheap relative to global)
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            gmax = global_buy.get(res, 1)
            if price / gmax <= buy_thresh:
                amt = min(budget / price, qty)
                if amt > 0:
                    buys[res] = buys.get(res, 0) + amt
                    budget -= amt * price

    # PHASE 2: Leftover cash -> 1-node profit opportunities
    if budget > 0:
        trades = []
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            already_bought = buys.get(res, 0)
            remaining = qty - already_bought
            if remaining > 0 and price > 0:
                next_info = next_shop.get(res)
                if next_info and next_info['buy'] > price:
                    ratio = next_info['buy'] / price
                    trades.append((ratio, res, price, remaining))

        trades.sort(reverse=True)
        for ratio, res, price, remaining in trades:
            if budget <= 0:
                break
            amt = min(budget / price, remaining)
            if amt > 0:
                buys[res] = buys.get(res, 0) + amt
                budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': next_pos
    }
