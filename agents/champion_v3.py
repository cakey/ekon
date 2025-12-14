"""
Champion Agent v3 - Best configuration from experimental iteration 3.

=== EXPERIMENT FINDINGS (Iteration 3) ===

Built on champion_v2 ($6,241/r @ 0.094ms)

TESTED:
- sell_threshold: 0.5-0.9 (only sell if price >= X% of global max)
- buy_for_global: Buy based on global max potential
- move_toward_sale: Bias movement toward best sale locations

RESULTS:
- sell_threshold=0.75: +$576/round (BEST)
- Plateau from 0.73-0.76, all give same improvement
- global_buy: Still disasters (-$6,319/round) - don't use
- move_toward_sale: Hurts performance

KEY INSIGHT:
The "carry to destination" strategy works, but ONLY for selling:
- Buy based on immediate neighbor profit (v2 behavior)
- Hold items until you can sell at 75%+ of global max
- Don't try to buy based on global prices (still broken)

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2, ALL neighbors
- Quantity cap: NONE
- Sell threshold: 0.75 (only sell at 75%+ of global max)
- Buy strategy: immediate neighbor (not global)

=== PERFORMANCE ===
- $/round:    +$6,857
- ms/round:   0.17ms
- Efficiency: 40,335 ($/round/ms)

Compare to previous:
- champion_v1: $5,052/r @ 0.057ms
- champion_v2: $6,241/r @ 0.094ms
- champion_v3: $6,857/r @ 0.17ms ← +10% over v2
"""

import random
_r = random.choice

SELL_THRESHOLD = 0.75  # Only sell at 75%+ of global max


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

    # Compute global max buy prices
    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    # Sell inventory - but only if price >= 75% of global max
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            local_price = my_shop[res]['buy']
            if local_price >= gmax * SELL_THRESHOLD:
                sells[res] = qty
                coin += qty * local_price

    if not neighbors:
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

    # 2-step lookahead with ALL neighbors
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

    # Buy profitable resources (based on immediate neighbor, not global)
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
