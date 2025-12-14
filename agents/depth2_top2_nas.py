"""
Experimental Agent v15 - Depth2 Top2 + NAS

Combine two proven techniques:
- depth2_top2: fast depth-2 lookahead (fills blitz→v1 gap)
- NAS: neighbor-aware selling (helped blitz by +$212)

NAS helped blitz because both are depth-1 style.
depth2_top2 is depth-2 - might interact differently.
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

    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
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
                    score += (to_info['buy'] - price) * qty
        return score

    def get_top_neighbors(from_pos, n=2):
        """Get top N neighbors by edge score."""
        nbs = list(world[from_pos]['neighbours'].keys())
        if len(nbs) <= n:
            return nbs
        scored = [(nb, score_edge(from_pos, nb)) for nb in nbs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [nb for nb, _ in scored[:n]]

    # 2-step lookahead with top-2 neighbors (from depth2_top2)
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

    if not best_n1:
        best_n1 = _r(neighbors) if neighbors else pos

    # NAS: Only sell if destination doesn't pay more
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
