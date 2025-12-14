"""
Champion Agent v4 - Best configuration from experimental iteration 4.

=== EXPERIMENT FINDINGS (Iteration 4) ===

Built on champion_v3 ($6,568/r @ 0.172ms, eff=38,149)

GOAL: Improve efficiency ($/round/ms) while maintaining good profit.

TESTED:
- blitz + sell_threshold: Hurts efficiency (threshold needs depth-2)
- depth1 + sell_threshold: Worse than blitz! Depth-2 is required.
- adaptive_depth: Skip depth-2 when depth-1 profit > threshold
- early_termination: Disaster at threshold 8000
- no_sort: Marginal improvement (+6.6%)
- sqrt_scoring: No improvement
- margin_only: Hurts profit

WINNER: Adaptive depth with threshold 4000
- Efficiency plateau at 48,000-49,000 for thresholds 1500-4000
- 4000 gives best profit within the plateau

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 1 when profit > 4000, depth 2 otherwise
- Quantity cap: NONE
- Sell threshold: 0.75 (only sell at 75%+ of global max)
- Buy strategy: immediate neighbor (not global)

=== PERFORMANCE ===
- $/round:    +$6,192
- ms/round:   0.127ms
- Efficiency: 48,703 ($/round/ms)

Compare to previous:
- champion_v1: $5,052/r @ 0.057ms (eff: 88,632)
- champion_v2: $6,241/r @ 0.094ms (eff: 66,394)
- champion_v3: $6,568/r @ 0.172ms (eff: 38,149)
- champion_v4: $6,192/r @ 0.127ms (eff: 48,703) <- +27% efficiency vs v3
"""

import random
_r = random.choice

ADAPTIVE_THRESHOLD = 4000  # Skip depth-2 if depth-1 profit > this
SELL_THRESHOLD = 0.75      # Only sell at 75%+ of global max


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
            if my_shop[res]['buy'] >= gmax * SELL_THRESHOLD:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
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

    # Depth 1 pass
    best_n1 = None
    best_s1 = 0
    for n in neighbors:
        s = score_edge(pos, n)
        if s > best_s1:
            best_s1 = s
            best_n1 = n

    # Adaptive: only do depth 2 if depth 1 profit is low
    if best_s1 < ADAPTIVE_THRESHOLD:
        best_score = best_s1
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
