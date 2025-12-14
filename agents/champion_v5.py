"""
Champion Agent v5 - v2 + Neighbor-Aware Selling

=== EXPERIMENT FINDINGS (Iteration 5) ===

Tested neighbor-aware selling across all frontier agents.
v2 + NAS dominates v2: +$428/round profit with no time cost.

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors (from v2)
- Quantity cap: NONE (from v2)
- Neighbor-aware selling: only sell if destination doesn't pay more
- No global price computation needed

=== PERFORMANCE ===
- $/round:    +$6,668
- ms/round:   0.087ms
- Efficiency: 76,644 ($/round/ms)

Dominates champion_v2 on the Pareto frontier.
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

    def score_edge(from_pos, to_pos):
        """Score arbitrage: buy at from, sell at to. No quantity cap."""
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

    # 2-step lookahead with ALL neighbors (from v2)
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        s1 = score_edge(pos, n1)
        n1_neighbors = list(world[n1]['neighbours'].keys())
        s2 = max((score_edge(n1, n2) for n2 in n1_neighbors), default=0)
        total = s1 + s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    # Neighbor-aware selling: only sell if destination doesn't pay more
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

    # Buy profitable resources for destination
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
