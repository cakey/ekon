"""
Global Arb Turbo - Ultra-fast global arbitrage with rotating neighbors

=== EXPERIMENT FINDINGS ===

Iteration 33c: Beat zen by using rotation instead of random.choice.

Key insight: random.choice() has overhead. Using deterministic rotation
through neighbors is faster while still providing enough exploration.

Strategy:
1. Precompute global max buy prices once
2. Rotate through neighbors deterministically (idx+1 % len)
3. Symmetric thresholds: buy ≤80%, sell ≥80%

=== PERFORMANCE ===
- $/round:    +$1,678
- ms/round:   0.0019ms
- Efficiency: 879,327

15x better than zen ($112 @ 0.0015ms) for only 1.27x the time.
DOMINATES zen_3 (same speed, 6.9x more profit).
"""


def agent(ws, state, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_node = world[pos]
    shop = my_node['resources']

    # Precompute global prices once
    if 'gb' not in state:
        gb = {}
        for node in world.values():
            for res, info in node['resources'].items():
                if info['buy'] > gb.get(res, 0):
                    gb[res] = info['buy']
        state['gb'] = gb
        state['idx'] = 0

    gb = state['gb']
    neighbors = list(my_node['neighbours'].keys())

    # Rotate through neighbors (faster than random.choice)
    if neighbors:
        state['idx'] = (state['idx'] + 1) % len(neighbors)
        next_pos = neighbors[state['idx']]
    else:
        next_pos = pos

    # Symmetric thresholds: 80/80
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in shop and shop[res]['buy'] / gb.get(res, 1) >= 0.80:
            sells[res] = qty
            coin += qty * shop[res]['buy']

    buys = {}
    for res, info in shop.items():
        if info['quantity'] > 0 and info['sell'] > 0 and coin > 0:
            if info['sell'] / gb.get(res, 1) <= 0.80:
                amt = min(coin / info['sell'], info['quantity'])
                buys[res] = amt
                coin -= amt * info['sell']

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': next_pos
    }
