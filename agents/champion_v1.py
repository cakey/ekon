"""
Champion Agent v1 - Best configuration from experimental iteration 1.

=== EXPERIMENT FINDINGS (2024-12) ===

Tested: lookahead depth (1-4), neighbor pruning (top 2-5, all), memoization, global prices

KEY INSIGHTS:
1. Depth 2 beats Depth 3 when using enough neighbors
   - depth2 ALL: $5,544/r @ 0.096ms
   - depth3 top4: $5,178/r @ 0.213ms (worse profit, 2x slower!)

2. More neighbors > more depth
   - Each extra neighbor at depth 2 adds ~$200-400 profit
   - Going depth 2→3 with limited neighbors hurts performance

3. Global price awareness HURTS (~$3,000/round loss!)
   - Buys items that can't be sold at immediate destination
   - Would need multi-hop carrying logic to work

4. Memoization only helps at depth 3+ (overhead > benefit at depth 2)

=== THIS AGENT'S CONFIG ===
- Lookahead: depth 2
- Neighbors: top 4 (sweet spot for profit/speed)
- No global prices
- No memoization (not beneficial at depth 2)

=== PERFORMANCE ===
- $/round:    +$5,049
- ms/round:   0.054ms
- Efficiency: 93,568 ($/round/ms)

Compare to:
- depth1 baseline: $3,124/r @ 0.009ms (eff: 351,141)
- depth2 ALL:      $5,544/r @ 0.096ms (eff: 57,525)

This config gives 77% of max profit at 56% of the time cost.
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
        """Score an edge by arbitrage profit: buy at from, sell at to."""
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0

        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * min(qty, 100)

        return score

    def get_top_neighbors(from_pos, n=4):
        """Get top N neighbors by edge score."""
        nbs = list(world[from_pos]['neighbours'].keys())
        if len(nbs) <= n:
            return nbs
        scored = [(nb, score_edge(from_pos, nb)) for nb in nbs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [nb for nb, _ in scored[:n]]

    # 2-step lookahead with top 4 neighbors
    best_n1 = None
    best_score = -1

    for n1 in get_top_neighbors(pos, 4):
        s1 = score_edge(pos, n1)

        top_n2 = get_top_neighbors(n1, 4)
        s2 = max((score_edge(n1, n2) for n2 in top_n2), default=0)

        total = s1 + s2 * 0.9  # Discount future slightly
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
