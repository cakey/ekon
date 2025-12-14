"""
Champion Agent v8 - Cash-Adaptive Global Thresholds

=== EXPERIMENT FINDINGS ===

Iteration 25: Dynamic thresholds based on cash on hand.

Key insight: Liquidity constraints matter early, diminish as capital grows.
- When poor (< $500): Accept 70% of global max (build capital)
- When rich (> $10000): Wait for 98% of global max (be picky)
- Between: Interpolate linearly

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors
- Discount factor: 0.7
- Sell threshold: 70% (poor) → 98% (rich), interpolated by cash
- Buy: weighted by closeness to global max

=== PERFORMANCE ===
- $/round:    +$7,184
- ms/round:   0.148ms
- vs v7:      +$115/round (+1.6%)
"""

import random


def agent(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    meta = ws['meta']
    my_node = world[pos]
    my_shop = my_node['resources']

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Compute global max buy prices
    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    # 2-step lookahead
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        n1_node = world[n1]
        n1_shop = n1_node['resources']

        s1 = 0
        for res, info in my_shop.items():
            qty = info['quantity']
            price = info['sell']
            if qty > 0 and price > 0:
                to_info = n1_shop.get(res)
                if to_info and to_info['buy'] > price:
                    s1 += (to_info['buy'] - price) * qty

        s2_best = 0
        for n2 in n1_node['neighbours'].keys():
            n2_shop = world[n2]['resources']
            s2 = 0
            for res, info in n1_shop.items():
                qty = info['quantity']
                price = info['sell']
                if qty > 0 and price > 0:
                    to_info = n2_shop.get(res)
                    if to_info and to_info['buy'] > price:
                        s2 += (to_info['buy'] - price) * qty
            if s2 > s2_best:
                s2_best = s2

        total = s1 + s2_best * 0.7
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = random.choice(neighbors)

    dest_shop = world[best_n1]['resources']

    # Cash-adaptive threshold
    low_cash, high_cash = 500, 10000
    loose_thresh, tight_thresh = 0.70, 0.98

    if coin <= low_cash:
        high_thresh = loose_thresh
    elif coin >= high_cash:
        high_thresh = tight_thresh
    else:
        ratio = (coin - low_cash) / (high_cash - low_cash)
        high_thresh = loose_thresh + ratio * (tight_thresh - loose_thresh)

    low_thresh = high_thresh - 0.20

    # Global-aware selling with cash-adaptive threshold
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            dest_info = dest_shop.get(res)
            dest_price = dest_info['buy'] if dest_info else 0
            gmax_ratio = local_price / gmax if gmax > 0 else 0

            if gmax_ratio >= high_thresh or (gmax_ratio >= low_thresh and local_price >= dest_price):
                sells[res] = qty
                coin += qty * local_price

    # Global-aware buying
    next_shop = dest_shop
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                margin = next_info['buy'] - price
                gmax = global_buy.get(res, next_info['buy'])
                closeness = next_info['buy'] / gmax if gmax > 0 else 0
                score = margin * closeness
                trades.append((score, res, price, qty))

    trades.sort(reverse=True)
    buys = {}
    budget = coin
    for score, res, price, qty in trades:
        if budget <= 0:
            break
        amt = min(budget / price, qty)
        if amt > 0:
            buys[res] = amt
            budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_n1
    }
