"""
Hybrid Greedy Agent - Greedy movement + precomputed global selling

=== EXPERIMENT FINDINGS ===

Iteration 28: Combine greedy movement with cash-adaptive global selling.

Key insight:
- Greedy 1-step movement (like blitz) for speed
- Precomputed global prices for smart selling
- No buy filtering (buy everything profitable)

=== THIS AGENT'S CONFIG ===
- Movement: Greedy (best immediate profit neighbor)
- Selling: Cash-adaptive threshold (60%→95% of global max)
- Buying: All profitable items, no filtering
- Global prices: Precomputed once at round 0

=== PERFORMANCE ===
- $/round:    +$2,761
- ms/round:   0.0077ms
- Efficiency: 358,634

On Pareto frontier between zen_all and blitz.
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

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': {}, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Greedy: pick best neighbor
    best_n = None
    best_score = -1
    for n in neighbors:
        n_shop = world[n]['resources']
        score = 0
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                n_info = n_shop.get(res)
                if n_info and n_info['buy'] > price:
                    score += (n_info['buy'] - price) * qty
        if score > best_score:
            best_score = score
            best_n = n

    if best_n is None:
        best_n = random.choice(neighbors)

    next_shop = world[best_n]['resources']

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
        'move': best_n
    }
