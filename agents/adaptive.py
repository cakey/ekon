"""
Experimental Agent v11 - Adaptive strategy (early/late game)

Hypothesis: Resources deplete over 200 rounds. Optimal strategy changes:
- Early game: Resources abundant, buy aggressively, explore widely
- Late game: Resources scarce, be more selective, exploit known good routes

Current agents use same strategy throughout. Adapting might help.

Approach: Use persistent state to track game phase and adjust behavior.
- Rounds 0-100: Aggressive (check more neighbors, buy more)
- Rounds 100-200: Conservative (focus on best options)
"""

import random
_r = random.choice


def agent(world_state, state, *args, **kwargs):
    y = world_state['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = world_state['world']
    my_shop = world[pos]['resources']
    meta = world_state['meta']

    current_round = meta['current_round']
    total_rounds = meta['total_rounds']

    # Adaptive parameters based on game phase
    progress = current_round / total_rounds
    if progress < 0.5:
        # Early game: explore more, check more neighbors
        top_n = 4  # Check more neighbors
        future_discount = 0.95  # Value future more
    else:
        # Late game: focus on best immediate opportunities
        top_n = 2  # Check fewer neighbors (faster)
        future_discount = 0.8  # Value immediate more

    neighbors = list(world[pos]['neighbours'].keys())

    # Last round - sell everything
    if current_round == total_rounds - 1:
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
                    score += (to_info['buy'] - price) * qty
        return score

    def get_top_neighbors(from_pos, n):
        """Get top N neighbors by edge score."""
        nbs = list(world[from_pos]['neighbours'].keys())
        if len(nbs) <= n:
            return nbs
        scored = [(nb, score_edge(from_pos, nb)) for nb in nbs]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [nb for nb, _ in scored[:n]]

    # 2-step lookahead with adaptive neighbor count
    best_n1 = None
    best_score = -1

    for n1 in get_top_neighbors(pos, top_n):
        s1 = score_edge(pos, n1)
        top_n2 = get_top_neighbors(n1, top_n)
        s2 = max((score_edge(n1, n2) for n2 in top_n2), default=0)
        total = s1 + s2 * future_discount
        if total > best_score:
            best_score = total
            best_n1 = n1

    # Random exploration if no opportunity
    if not best_n1:
        best_n1 = _r(neighbors) if neighbors else pos

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
