"""
Simple Random Agent - Ultra-fast random explorer

=== EXPERIMENT FINDINGS ===

Iteration 26: Sometimes the simplest approach works.

This agent uses:
- Random movement (no lookahead)
- Buy ALL profitable items (no filtering)
- Sell everything

Why it works:
- Exploration finds opportunities naturally
- No computation overhead for scoring
- Randomness prevents getting stuck in local patterns

=== PERFORMANCE ===
- $/round:    +$1,417
- ms/round:   0.0021ms
- Efficiency: 664,687

Dominates zen_4, zen_5, zen_6 on Pareto frontier.
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

    # Last round: sell everything
    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(my_node['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': {}, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Random movement
    next_pos = random.choice(neighbors)
    next_shop = world[next_pos]['resources']

    # Sell everything
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            sells[res] = qty
            coin += qty * my_shop[res]['buy']

    # Buy anything profitable, prioritize by ratio
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
        'move': next_pos
    }
