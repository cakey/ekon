"""
Champion Agent v2 - Best configuration from experimental iteration 2.

=== EXPERIMENT FINDINGS (Iteration 2) ===

Built on champion_v1 (depth2 top4 cap100: $5,052/r @ 0.057ms)

TESTED:
- future_discount: 0.7-1.0 (no significant impact)
- budget_reserve: 10-20% (hurts profit)
- qty_cap: 50, 100, 200, none (NONE is best!)
- buy_all_profitable: True/False (True is crucial)
- hub_bonus: 10-100 (HURTS badly)
- min_margin: 1-5 (HURTS - don't filter low margin)
- top_n: 4-8, all (MORE is better, ALL is best)

KEY INSIGHT:
Removing qty_cap=100 gave +$458/round alone.
Using ALL neighbors instead of top-4 gave +$730/round more.
Combined: +$1,189/round (+23.5% improvement!)

Surprising: no_cap ALL is FASTER than no_cap top8 (0.094 vs 0.104ms)
because sorting overhead exceeds pruning benefit when N is large.

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2
- Neighbors: ALL (no pruning)
- Quantity cap: NONE
- No global prices, no hub bonus, no margin filter

=== PERFORMANCE ===
- $/round:    +$6,241
- ms/round:   0.094ms
- Efficiency: 66,087 ($/round/ms)

Compare to v1:
- champion_v1: $5,052/r @ 0.057ms (eff: 89,207)
- champion_v2: $6,241/r @ 0.094ms (eff: 66,087) ← +23.5% profit
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

    neighbors = list(world[pos]['neighbours'].keys())

    # Last round - sell everything
    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    # Sell all inventory
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            sells[res] = qty
            coin += qty * my_shop[res]['buy']

    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge(from_pos, to_pos):
        """Score an edge by arbitrage profit: buy at from, sell at to.
        NO quantity cap - use full potential."""
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0

        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * qty  # No cap!

        return score

    # 2-step lookahead with ALL neighbors (no pruning - faster than sorting!)
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        s1 = score_edge(pos, n1)

        # Check all second-hop neighbors too
        n1_neighbors = list(world[n1]['neighbours'].keys())
        s2 = max((score_edge(n1, n2) for n2 in n1_neighbors), default=0)

        total = s1 + s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    # Buy profitable resources for chosen destination
    trades = []
    next_shop = world[best_n1]['resources']

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
