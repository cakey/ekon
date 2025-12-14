"""
Champion Agent v1 - Depth-2 Top-4 with Inlined Scoring

=== EXPERIMENT FINDINGS ===

Iteration 1: Depth 2 beats depth 3 when using enough neighbors.
Iteration 22: Inlined scoring gives 1.08x speedup.

KEY INSIGHTS:
1. More neighbors > more depth (each extra neighbor adds ~$200-400)
2. Global price awareness HURTS (~$3,000/round loss!)
3. Inlining hot paths beats memoization for simple functions

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, top 4 neighbors (inlined)
- Quantity cap: 100 in scoring
- No global prices

=== PERFORMANCE ===
- $/round:    +$5,079
- ms/round:   0.050ms
- Efficiency: 101,580
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

    # Sell all inventory
    sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
    for res, qty in sells.items():
        coin += qty * my_shop[res]['buy']

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Get top 4 neighbors by inlined scoring
    neighbor_scores = []
    for n1 in neighbors:
        n1_shop = world[n1]['resources']
        s = 0
        for res, info in my_shop.items():
            qty = min(info['quantity'], 100)
            price = info['sell']
            if qty > 0 and price > 0:
                to_info = n1_shop.get(res)
                if to_info:
                    buy_price = to_info['buy']
                    if buy_price > price:
                        s += (buy_price - price) * qty
        neighbor_scores.append((s, n1))

    neighbor_scores.sort(reverse=True)
    top_neighbors = [n for _, n in neighbor_scores[:4]]

    # 2-step lookahead with inlined scoring
    best_n1 = None
    best_score = -1

    for n1 in top_neighbors:
        n1_node = world[n1]
        n1_shop = n1_node['resources']

        s1 = 0
        for res, info in my_shop.items():
            qty = min(info['quantity'], 100)
            price = info['sell']
            if qty > 0 and price > 0:
                to_info = n1_shop.get(res)
                if to_info:
                    buy_price = to_info['buy']
                    if buy_price > price:
                        s1 += (buy_price - price) * qty

        # Best n2 score
        s2_best = 0
        for n2 in n1_node['neighbours'].keys():
            n2_shop = world[n2]['resources']
            s2 = 0
            for res, info in n1_shop.items():
                qty = min(info['quantity'], 100)
                price = info['sell']
                if qty > 0 and price > 0:
                    to_info = n2_shop.get(res)
                    if to_info:
                        buy_price = to_info['buy']
                        if buy_price > price:
                            s2 += (buy_price - price) * qty
            if s2 > s2_best:
                s2_best = s2

        total = s1 + s2_best * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = random.choice(neighbors)

    # Buy profitable resources
    next_shop = world[best_n1]['resources']
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
        'move': best_n1
    }
