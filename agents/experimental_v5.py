"""
Experimental Agent v5 - Testing "Neighbor-aware selling" across all frontier agents.

=== IDEA ===
Current: Sell everything at current shop before moving
New: Only sell if destination shop doesn't pay more for that resource

This is a simpler version of sell_threshold (v3) that doesn't require global price scan.
Just compare current shop price vs destination shop price.

=== TEST MATRIX ===
Testing this idea on each frontier agent:
- blitz + idea -> blitz_nas
- v1 + idea -> v1_nas
- v2 + idea -> v2_nas
- v3 + idea -> v3_nas (already has sell_threshold, may conflict or improve)

=== HYPOTHESIS ===
- Should help agents that don't already have sell awareness (blitz, v1, v2)
- May conflict with v3's global threshold approach
- Minimal time overhead (just one shop lookup per resource)
"""

import random
_r = random.choice


# =============================================================================
# BLITZ + NEIGHBOR-AWARE SELLING
# Base: depth-1, sell everything, buy for best neighbor
# Change: only sell if destination doesn't pay more
# =============================================================================
def blitz_nas(ws, *a, **k):
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

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        # No neighbors - sell everything, stay put
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # First find best neighbor (same as blitz)
    best_n = pos
    best_profit = 0
    best_buys = None

    for n in neighbors:
        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin  # Use original coin, sells happen after

        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0 and budget > 0:
                n_info = n_shop.get(res)
                if n_info and n_info['buy'] > price:
                    amt = min(budget / price, qty)
                    buys[res] = amt
                    budget -= amt * price
                    profit += (n_info['buy'] - price) * amt

        if profit > best_profit:
            best_profit = profit
            best_n = n
            best_buys = buys

    if not best_buys:
        best_n = _r(neighbors) if neighbors else pos

    # Now decide what to sell - only if destination doesn't pay more
    dest_shop = world[best_n]['resources']
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            current_price = my_shop[res]['buy']
            dest_info = dest_shop.get(res)
            dest_price = dest_info['buy'] if dest_info else 0
            # Only sell if destination doesn't pay more
            if current_price >= dest_price:
                sells[res] = qty
                coin += qty * current_price

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys or {},
        'move': best_n
    }


# =============================================================================
# V1 + NEIGHBOR-AWARE SELLING
# Base: depth-2 with top-4 neighbors
# Change: only sell if destination doesn't pay more
# =============================================================================
def v1_nas(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_shop = world[pos]['resources']
    meta = ws['meta']

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge(from_pos, to_pos):
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * min(qty, 100)  # v1 had qty cap
        return score

    # Score neighbors and take top 4
    scored = [(score_edge(pos, n), n) for n in neighbors]
    scored.sort(reverse=True)
    top_neighbors = [n for _, n in scored[:4]]

    best_n1 = None
    best_score = -1

    for n1 in top_neighbors:
        s1 = score_edge(pos, n1)
        n1_neighbors = list(world[n1]['neighbours'].keys())
        scored2 = [(score_edge(n1, n2), n2) for n2 in n1_neighbors]
        scored2.sort(reverse=True)
        s2 = scored2[0][0] if scored2 else 0
        total = s1 + s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    # Neighbor-aware selling
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

    # Buy for destination
    next_shop = world[best_n1]['resources']
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                trades.append((next_info['buy'] / price, res, price, min(qty, 100)))

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


# =============================================================================
# V2 + NEIGHBOR-AWARE SELLING
# Base: depth-2 with ALL neighbors, no qty cap
# Change: only sell if destination doesn't pay more
# =============================================================================
def v2_nas(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_shop = world[pos]['resources']
    meta = ws['meta']

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge(from_pos, to_pos):
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    score += (to_info['buy'] - price) * qty  # No cap
        return score

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

    # Neighbor-aware selling
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

    # Buy for destination
    next_shop = world[best_n1]['resources']
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                trades.append((next_info['buy'] / price, res, price, qty))

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


# =============================================================================
# V3 + NEIGHBOR-AWARE SELLING
# Base: depth-2 with ALL neighbors, sell_threshold=0.75
# Change: Replace global threshold with neighbor-aware check
# =============================================================================
def v3_nas(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_shop = world[pos]['resources']
    meta = ws['meta']

    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        sells = {r: q for r, q in my_res.items() if r in my_shop and q > 0}
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge(from_pos, to_pos):
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

    # Neighbor-aware selling (replaces global threshold)
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

    # Buy for destination
    next_shop = world[best_n1]['resources']
    trades = []
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            next_info = next_shop.get(res)
            if next_info and next_info['buy'] > price:
                trades.append((next_info['buy'] / price, res, price, qty))

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
