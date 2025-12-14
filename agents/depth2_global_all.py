"""
Depth2 Global All - depth2 with ALL neighbors + global arb

=== EXPERIMENT FINDINGS ===

Iteration 32: Check ALL neighbors for maximum profit.

Strategy: Same as depth2_global but check ALL neighbors (no pruning).
Slower but highest profit.

=== PERFORMANCE ===
- $/round:    +$9,017
- ms/round:   0.0834ms
- Efficiency: 108,131

Max profit frontier point.
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

    def score_edge(from_pos, to_pos):
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * qty
        return score

    # ALL neighbors depth-2 lookahead
    scored = []
    for n1 in neighbors:
        n1_neighbors = list(world[n1]['neighbours'].keys())  # ALL neighbors
        best_n2_score = 0
        for n2 in n1_neighbors:
            best_n2_score = max(best_n2_score, score_edge(n1, n2))
        total = score_edge(pos, n1) + 0.9 * best_n2_score
        scored.append((total, n1))

    scored.sort(reverse=True)
    best_neighbor = scored[0][1] if scored else random.choice(neighbors)
    next_shop = world[best_neighbor]['resources']

    if coin < 500:
        sell_thresh = 0.60
    elif coin > 10000:
        sell_thresh = 0.90
    else:
        t = (coin - 500) / 9500
        sell_thresh = 0.60 + 0.30 * t

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

    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                ratio = next_info['buy'] / price
                trades.append((ratio, res, price, qty))

    trades.sort(reverse=True)
    for ratio, res, price, qty in trades:
        if budget <= 0:
            break
        amt = min(budget / price, qty)
        if amt > 0:
            buys[res] = buys.get(res, 0) + amt
            budget -= amt * price

    if budget > 0:
        buy_thresh = 0.80
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            already = buys.get(res, 0)
            remaining = qty - already
            if remaining > 0 and price > 0 and budget > 0:
                gmax = global_buy.get(res, 1)
                if price / gmax <= buy_thresh:
                    amt = min(budget / price, remaining)
                    if amt > 0:
                        buys[res] = buys.get(res, 0) + amt
                        budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_neighbor
    }
