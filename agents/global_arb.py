"""
Global Arbitrage Agent - Pure buy-low-sell-high based on global prices

=== EXPERIMENT FINDINGS ===

Iteration 29: Pure global arbitrage with cash-adaptive thresholds.

Key insight:
- Buy when current node price is CHEAP relative to global max
- Sell when current node price is EXPENSIVE relative to global max
- Move randomly - trust you'll encounter both cheap and expensive nodes
- No neighbor lookahead needed!

Cash-adaptive thresholds:
- Poor ($<500): buy at <=85% of global, sell at >=65% of global (looser)
- Rich ($>10000): buy at <=75% of global, sell at >=85% of global (tighter)

=== PERFORMANCE ===
- $/round:    +$4,050
- ms/round:   0.0030ms
- Efficiency: 1,343,195

DOMINATES: simple_global, zen_all, blitz, blitz_nas, hybrid_greedy
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

    # Precompute global prices once
    if 'global_buy' not in state:
        global_buy = {}
        for node in world.values():
            for res, info in node['resources'].items():
                if info['buy'] > global_buy.get(res, 0):
                    global_buy[res] = info['buy']
        state['global_buy'] = global_buy

    global_buy = state['global_buy']

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

    # Cash-adaptive thresholds
    # Poor: looser (buy more, sell more readily)
    # Rich: tighter (only buy cheap, only sell expensive)
    if coin < 500:
        buy_thresh = 0.85   # Buy at up to 85% of global
        sell_thresh = 0.65  # Sell at 65%+ of global
    elif coin > 10000:
        buy_thresh = 0.75   # Only buy at 75% or less of global
        sell_thresh = 0.85  # Only sell at 85%+ of global
    else:
        t = (coin - 500) / 9500
        buy_thresh = 0.85 + (0.75 - 0.85) * t   # 85% -> 75%
        sell_thresh = 0.65 + (0.85 - 0.65) * t  # 65% -> 85%

    # SELL at expensive nodes (price >= sell_thresh of global)
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            local_price = my_shop[res]['buy']
            gmax = global_buy.get(res, 1)
            if local_price / gmax >= sell_thresh:
                sells[res] = qty
                coin += qty * local_price

    # BUY at cheap nodes (price <= buy_thresh of global)
    buys = {}
    budget = coin
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            gmax = global_buy.get(res, 1)
            if price / gmax <= buy_thresh:
                amt = min(budget / price, qty)
                if amt > 0:
                    buys[res] = amt
                    budget -= amt * price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': next_pos
    }
