"""
Experimental Agent v4 - Efficiency-focused brainstorm.

=== HISTORICAL CONTEXT ===

What we've learned so far:
1. More neighbors > more depth (breadth beats depth)
2. No caps/filters - full information helps
3. Sell threshold 0.75 helps (+$576/round)
4. Global buying broken - must buy for immediate neighbor
5. Hub bonus HURTS - structural heuristics fail
6. Sorting overhead is significant

Current efficiency problem:
- blitz: $3,654/r @ 0.008ms = 486,452 eff
- champion_v3: $6,947/r @ 0.17ms = 41,233 eff
- blitz is 12x MORE EFFICIENT!

=== HYPOTHESES TO TEST ===

MOST PROMISING (based on history):
1. blitz + sell_threshold - combine fastest agent with best finding
2. Adaptive depth - depth 1 when obvious, depth 2 only when unclear
3. Early termination - stop if profit > threshold
4. No-sort single pass - find best without sorting

WORTH TESTING:
5. Better scoring - margin * sqrt(qty) instead of margin * qty
6. Precompute neighbors - avoid dict.keys() overhead
7. Integer math - avoid float operations

PROBABLY WON'T WORK (but test anyway):
8. Reverse search - start from sell locations
9. Monte Carlo sampling - random path selection
"""

import random
_r = random.choice


# =============================================================================
# APPROACH 1: Blitz + Sell Threshold
# Hypothesis: Blitz is fast, sell_threshold helps. Combine them.
# Expected: High efficiency, decent profit
# =============================================================================
def blitz_threshold(ws, *a, **k):
    y = ws['you']
    pos = y['position']
    coin = y['coin']
    my_res = y['resources']
    world = ws['world']
    my_shop = world[pos]['resources']
    meta = ws['meta']

    # Last round
    if meta['current_round'] == meta['total_rounds'] - 1:
        return {
            'resources_to_sell_to_shop': {r: q for r, q in my_res.items() if r in my_shop and q > 0},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    # Compute global max (needed for threshold)
    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    # Sell with threshold (75% of global max)
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Blitz-style: single pass, find best neighbor
    best_n = pos
    best_profit = 0
    best_buys = None

    for n in neighbors:
        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin

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

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys or {},
        'move': best_n
    }


# =============================================================================
# APPROACH 2: Adaptive Depth
# Hypothesis: Use depth 1 when profit is obvious (>threshold), depth 2 otherwise
# Expected: Faster than always-depth-2, similar profit
# =============================================================================
def adaptive_depth(ws, *a, **k):
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

    # Global prices for sell threshold
    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
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

    # Depth 1 pass
    best_n1 = None
    best_s1 = 0
    for n in neighbors:
        s = score_edge(pos, n)
        if s > best_s1:
            best_s1 = s
            best_n1 = n

    # Adaptive: only do depth 2 if depth 1 profit is low
    PROFIT_THRESHOLD = 5000  # If immediate profit > this, skip depth 2

    if best_s1 < PROFIT_THRESHOLD:
        # Do depth 2 search
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

    # Buy for chosen destination
    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin
    trades = []

    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
                trades.append((n_info['buy'] / price, res, price, qty))

    trades.sort(reverse=True)
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
# APPROACH 3: Early Termination
# Hypothesis: Stop searching once you find a "good enough" opportunity
# Expected: Faster with minimal profit loss
# =============================================================================
def early_termination(ws, *a, **k):
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

    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    GOOD_ENOUGH = 8000  # Stop if we find this much profit

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

        # Early termination
        if s1 >= GOOD_ENOUGH:
            best_n1 = n1
            break

        n1_neighbors = list(world[n1]['neighbours'].keys())
        s2 = max((score_edge(n1, n2) for n2 in n1_neighbors), default=0)
        total = s1 + s2 * 0.9

        if total > best_score:
            best_score = total
            best_n1 = n1

        # Early termination on total
        if total >= GOOD_ENOUGH:
            break

    if not best_n1:
        best_n1 = _r(neighbors)

    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin
    trades = []

    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
                trades.append((n_info['buy'] / price, res, price, qty))

    trades.sort(reverse=True)
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
# APPROACH 4: No-Sort Single Pass
# Hypothesis: Sorting is expensive. Track best 2 in single pass.
# Expected: Faster, same results
# =============================================================================
def no_sort(ws, *a, **k):
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

    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge_fast(from_pos, to_pos):
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

    # Single pass - no sorting
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        s1 = score_edge_fast(pos, n1)
        n1_neighbors = world[n1]['neighbours']

        # Find best second hop without sorting
        best_s2 = 0
        for n2 in n1_neighbors:
            s2 = score_edge_fast(n1, n2)
            if s2 > best_s2:
                best_s2 = s2

        total = s1 + best_s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    # Buy without sorting - just take all profitable
    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin

    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
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
# APPROACH 5: Better Scoring (sqrt qty)
# Hypothesis: margin * qty overweights high-quantity items
# Expected: Might help, might not
# =============================================================================
import math

def sqrt_scoring(ws, *a, **k):
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

    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge_sqrt(from_pos, to_pos):
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        score = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    # sqrt(qty) instead of qty
                    score += (to_info['buy'] - price) * math.sqrt(qty)
        return score

    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        s1 = score_edge_sqrt(pos, n1)
        n1_neighbors = world[n1]['neighbours']
        best_s2 = 0
        for n2 in n1_neighbors:
            s2 = score_edge_sqrt(n1, n2)
            if s2 > best_s2:
                best_s2 = s2
        total = s1 + best_s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
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
# APPROACH 6: Margin-only scoring (ignore quantity)
# Hypothesis: Maybe just pick highest margin, quantity doesn't matter for direction
# =============================================================================
def margin_only(ws, *a, **k):
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

    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    def score_edge_margin(from_pos, to_pos):
        from_shop = world[from_pos]['resources']
        to_shop = world[to_pos]['resources']
        best_margin = 0
        for res, info in from_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                to_info = to_shop.get(res)
                if to_info and to_info['buy'] > price:
                    margin = to_info['buy'] - price
                    if margin > best_margin:
                        best_margin = margin
        return best_margin

    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        s1 = score_edge_margin(pos, n1)
        n1_neighbors = world[n1]['neighbours']
        best_s2 = 0
        for n2 in n1_neighbors:
            s2 = score_edge_margin(n1, n2)
            if s2 > best_s2:
                best_s2 = s2
        total = s1 + best_s2 * 0.9
        if total > best_score:
            best_score = total
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
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
# APPROACH 7: Depth 1 only + sell threshold
# Hypothesis: Maybe depth 2 isn't worth it at all
# =============================================================================
def depth1_threshold(ws, *a, **k):
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

    global_buy = {}
    for node in world.values():
        for res, info in node['resources'].items():
            if info['buy'] > global_buy.get(res, 0):
                global_buy[res] = info['buy']

    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            gmax = global_buy.get(res, 1)
            if my_shop[res]['buy'] >= gmax * 0.75:
                sells[res] = qty
                coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Depth 1 only
    best_n1 = None
    best_score = -1

    for n1 in neighbors:
        n1_shop = world[n1]['resources']
        score = 0
        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                n_info = n1_shop.get(res)
                if n_info and n_info['buy'] > price:
                    score += (n_info['buy'] - price) * qty
        if score > best_score:
            best_score = score
            best_n1 = n1

    if not best_n1:
        best_n1 = _r(neighbors)

    next_shop = world[best_n1]['resources']
    buys = {}
    budget = coin
    for res, info in my_shop.items():
        qty, price = info['quantity'], info['sell']
        if qty > 0 and price > 0 and budget > 0:
            n_info = next_shop.get(res)
            if n_info and n_info['buy'] > price:
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
# APPROACH 8: Pure blitz (baseline for efficiency comparison)
# Note: Implementation moved to _pure_blitz below, pure_blitz calls it
# =============================================================================


# =============================================================================
# THRESHOLD TUNING FOR ADAPTIVE DEPTH
# =============================================================================
def make_adaptive(threshold):
    """Factory to create adaptive depth agents with different thresholds."""
    def agent(ws, *a, **k):
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

        global_buy = {}
        for node in world.values():
            for res, info in node['resources'].items():
                if info['buy'] > global_buy.get(res, 0):
                    global_buy[res] = info['buy']

        sells = {}
        for res, qty in my_res.items():
            if qty > 0 and res in my_shop:
                gmax = global_buy.get(res, 1)
                if my_shop[res]['buy'] >= gmax * 0.75:
                    sells[res] = qty
                    coin += qty * my_shop[res]['buy']

        neighbors = list(world[pos]['neighbours'].keys())
        if not neighbors:
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
        best_s1 = 0
        for n in neighbors:
            s = score_edge(pos, n)
            if s > best_s1:
                best_s1 = s
                best_n1 = n

        if best_s1 < threshold:
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

        next_shop = world[best_n1]['resources']
        buys = {}
        budget = coin
        trades = []

        for res, info in my_shop.items():
            qty, price = info['quantity'], info['sell']
            if qty > 0 and price > 0:
                n_info = next_shop.get(res)
                if n_info and n_info['buy'] > price:
                    trades.append((n_info['buy'] / price, res, price, qty))

        trades.sort(reverse=True)
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
    return agent


# Create variants with different thresholds
adaptive_1000 = make_adaptive(1000)
adaptive_1500 = make_adaptive(1500)
adaptive_2000 = make_adaptive(2000)
adaptive_2500 = make_adaptive(2500)
adaptive_3000 = make_adaptive(3000)
adaptive_4000 = make_adaptive(4000)
adaptive_5000 = make_adaptive(5000)
adaptive_7000 = make_adaptive(7000)
adaptive_10000 = make_adaptive(10000)


# Original pure_blitz implementation
def _pure_blitz(ws, *a, **k):
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

    # Sell everything
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in my_shop:
            sells[res] = qty
            coin += qty * my_shop[res]['buy']

    neighbors = list(world[pos]['neighbours'].keys())
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    best_n = pos
    best_profit = 0
    best_buys = None

    for n in neighbors:
        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin

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

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys or {},
        'move': best_n
    }


# Alias for external use
pure_blitz = _pure_blitz
