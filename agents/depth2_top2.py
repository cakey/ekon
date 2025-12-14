"""
Experimental Agent v10 - Depth-2 with top-2 neighbors

Goal: Fill the blitz→v1 gap ($3,774 → $5,093)

v1: depth-2, top-4 neighbors = 16 edge scores
v10: depth-2, top-2 neighbors = 4 edge scores (4x faster)

Expected: ~$4,000-4,500/r at ~0.015-0.025ms
Must check: Is it on the Pareto frontier? (not dominated by blitz or v1)
"""

import random
_r = random.choice


def agent(world_state, *args, **kwargs):
    y = world_state['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = world_state['world']
    my_shop = world[pos]['resources']
    meta = world_state['meta']

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
        """Score arbitrage: buy at from, sell at to."""
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * qty  # No qty cap
        return score

    def get_top_neighbors(from_pos, n=2):
        """Get top N neighbors by edge score."""
        nbs = list(world[from_pos]['neighbours'].keys())
        if len(nbs) <= n:
            return nbs
        scored = [(nb, score_edge(from_pos, nb)) for nb in nbs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [nb for nb, _ in scored[:n]]

    # 2-step lookahead with top-2 neighbors
    best_n1 = None
    best_score = -1

    for n1 in get_top_neighbors(pos, 2):
        s1 = score_edge(pos, n1)
        top_n2 = get_top_neighbors(n1, 2)
        s2 = max((score_edge(n1, n2) for n2 in top_n2), default=0)
        total = s1 + s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    # Random exploration if no opportunity
    if not best_n1:
        best_n1 = _r(neighbors) if neighbors else pos

    # Buy profitable resources for chosen destination
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
