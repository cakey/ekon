"""
Max Profit - NEW MAX PROFIT AGENT

=== EXPERIMENT FINDINGS ===

Iteration 35: Buy/sell optimization research found that more aggressive
buying improves profit without sacrificing speed.

Key change from hybrid_champion:
- Buy threshold: 85% of global max (was 80%)
- Same sell thresholds (60%-90% cash-adaptive)

Why it works:
- More aggressive buying captures more arbitrage opportunities
- Items bought at 85% can still be sold at 90%+ for profit
- The 5% wider buy window significantly increases trade volume

=== PERFORMANCE ===
- $/round:    +$10,116
- ms/round:   0.0172ms
- Efficiency: 588,000

DOMINATES hybrid_champion:
- More profit (+$228/r, +2.3%)
- AND faster (0.0172ms vs 0.0191ms)
"""

import random


def agent(ws, state, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    meta = ws['meta']
    my_node = world[pos]
    my_shop = my_node['resources']

    if 'global_buy' not in state:
        global_buy = {}
        for node in world.values():
            for res, info in node['resources'].items():
                if info['buy'] > global_buy.get(res, 0):
                    global_buy[res] = info['buy']
        state['global_buy'] = global_buy

    global_buy = state['global_buy']

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': {}, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Hybrid movement scoring
    def edge_score(to_pos):
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * qty
        return score

    def global_score(n):
        n_shop = world[n]['resources']
        score = 0
        for res, info in n_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                gmax = global_buy.get(res, 1)
                if price / gmax <= 0.85:  # 85% threshold (was 80%)
                    score += (gmax - price) * qty
        return score

    scored = [(edge_score(n) + 0.5 * global_score(n), n) for n in neighbors]
    scored.sort(reverse=True)
    best_neighbor = scored[0][1] if scored[0][0] > 0 else random.choice(neighbors)
    next_shop = world[best_neighbor]['resources']

    # Cash-adaptive sell threshold (60%->90%)
    if coin < 500:
        sell_thresh = 0.60
    elif coin > 10000:
        sell_thresh = 0.90
    else:
        t = (coin - 500) / 9500
        sell_thresh = 0.60 + 0.30 * t

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            if local_price / gmax >= sell_thresh:
                sells[res] = qty
                coin += qty * local_price

    buys = {}
    budget = coin

    # Priority: items profitable at next node
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                ratio = next_info['buy'] / price
                trades.append((ratio, res, price, qty))

    trades.sort(reverse=True)
    for ratio, res, price, qty in trades:
        if budget <= 0:
            break
        amt = min(budget / price, qty)
        if amt > 0:
            buys[res] = buys.get(res, 0) + amt
            budget -= amt * price

    # Leftover: global arb buys at 85% threshold (was 80%)
    if budget > 0:
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            already = buys.get(res, 0)
            remaining = qty - already
            if remaining > 0 and price > 0 and budget > 0:
                gmax = global_buy.get(res, 1)
                if price / gmax <= 0.85:  # 85% threshold (was 80%)
                    amt = min(budget / price, remaining)
                    if amt > 0:
                        buys[res] = buys.get(res, 0) + amt
                        budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_neighbor
    }
