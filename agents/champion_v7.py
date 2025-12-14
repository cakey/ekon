"""
Champion Agent v7 - Global-Aware Buy/Sell Strategy

=== EXPERIMENT FINDINGS ===

Iteration 24: Global price awareness applied to BOTH buying and selling.

Key innovations:
1. SELL: At 95%+ of global max unconditionally, or 75%+ if dest is worse
2. BUY: Weight by closeness to global max (prioritize best resale opportunities)

This combines the best insights:
- From v3: Global sell threshold idea (but refined to 0.95/0.75)
- From v6: NAS fallback behavior
- NEW: Global-aware buying prioritization

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors
- Discount factor: 0.7
- Sell: global threshold 95%, NAS fallback at 75%
- Buy: weighted by closeness to global max

=== PERFORMANCE ===
- $/round:    +$6,996
- ms/round:   0.148ms
- Efficiency: 47,320

Dominates champion_v3 on the Pareto frontier.
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

    # 2-step lookahead with inlined scoring
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
                if to_info:
                    buy_price = to_info['buy']
                    if buy_price > price:
                        s1 += (buy_price - price) * qty

        s2_best = 0
        for n2 in n1_node['neighbours'].keys():
            n2_shop = world[n2]['resources']
            s2 = 0
            for res, info in n1_shop.items():
                qty = info['quantity']
                price = info['sell']
                if qty > 0 and price > 0:
                    to_info = n2_shop.get(res)
                    if to_info:
                        buy_price = to_info['buy']
                        if buy_price > price:
                            s2 += (buy_price - price) * qty
            if s2 > s2_best:
                s2_best = s2

        total = s1 + s2_best * 0.7
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = random.choice(neighbors)

    dest_shop = world[best_n1]['resources']

    # Global-aware selling
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            dest_info = dest_shop.get(res)
            dest_price = dest_info['buy'] if dest_info else 0
            gmax_ratio = local_price / gmax if gmax > 0 else 0

            if gmax_ratio >= 0.95 or (gmax_ratio >= 0.75 and local_price >= dest_price):
                sells[res] = qty
                coin += qty * local_price

    # Global-aware buying: weight by closeness to global max
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
