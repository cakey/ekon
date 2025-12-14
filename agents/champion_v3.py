"""
Champion Agent v3 - Global Sell Threshold + Inlined Hot Path

=== EXPERIMENT FINDINGS ===

Iteration 3: Global sell threshold (75%) adds +$576/r.
Iteration 22: Inlined scoring gives 1.08x speedup.

KEY INSIGHT: The "carry to destination" strategy works for selling:
- Hold items until you can sell at 75%+ of global max
- Buy based on immediate neighbor profit (not global)

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors (inlined)
- Discount factor: 0.9
- Sell threshold: 0.75 (only sell at 75%+ of global max)
- Buy strategy: immediate neighbor

=== PERFORMANCE ===
- $/round:    +$6,832
- ms/round:   0.156ms
- Efficiency: 43,795

Max profit agent under 0.5ms cap.
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
    neighbors = list(my_node['neighbours'].keys())

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    # Compute global max buy prices
    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    # Sell only at 75%+ of global max
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            local_price = my_shop[res]['buy']
            if local_price >= gmax * 0.75:
                sells[res] = qty
                coin += qty * local_price

    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # 2-step lookahead with inlined scoring
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        n1_node = world[n1]
        n1_shop = n1_node['resources']

        # Inlined score pos -> n1
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

        # Inlined score n1 -> n2
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
