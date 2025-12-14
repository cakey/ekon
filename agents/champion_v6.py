"""
Champion Agent v6 - Optimized Discount Factor + Inlined Hot Path

=== EXPERIMENT FINDINGS ===

Iteration 19: Discount factor d=0.7 outperforms d=0.9 by ~$80/r.
Iteration 22: Profile-guided inlining gives 1.25x speedup.

Key optimizations:
- Inlined score_edge hot path (was 56% of execution time)
- Cached world[pos] lookups
- Reduced function call overhead

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors
- Discount factor: 0.7
- Neighbor-aware selling: only sell if destination doesn't pay more

=== PERFORMANCE ===
- $/round:    +$6,723
- ms/round:   0.076ms
- Efficiency: 88,461

Dominates previous champion_v6 (0.095ms) on the Pareto frontier.
"""

import random


def agent(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    meta = ws['meta']

    # Cache current node
    my_node = world[pos]
    my_shop = my_node['resources']

    # Last round - sell everything
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

    # 2-step lookahead with inlined scoring
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        n1_node = world[n1]
        n1_shop = n1_node['resources']

        # Score edge pos -> n1 (inlined)
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

        # Score best n1 -> n2 edge (inlined)
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

        total = s1 + s2_best * 0.7  # Discount factor
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = random.choice(neighbors)

    # Neighbor-aware selling
    dest_shop = world[best_n1]['resources']
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            current_price = my_shop[res]['buy']
            dest_info = dest_shop.get(res)
            dest_price = dest_info['buy'] if dest_info else 0
            if current_price >= dest_price:
                sells[res] = qty
                coin += qty * current_price

    # Buy profitable resources
    next_shop = dest_shop
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
