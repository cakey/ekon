"""
Lookahead Agent

Strategy: Simulate all possible movement paths over the next N turns,
using greedy trading at each step. Pick the path that maximizes
expected wealth, then execute the first move.
"""

from . import utils as u

LOOKAHEAD_DEPTH = 4  # Balance between lookahead and speed
MAX_NEIGHBORS = 4  # Limit neighbors considered at each step


def get_global_prices(world):
    """Get max sell price for each resource globally."""
    prices = {}
    for node in world.values():
        for res, info in node['resources'].items():
            prices[res] = max(prices.get(res, 0), info['buy'])
    return prices


def simulate_step(world, pos, coin, resources, global_prices):
    """
    Simulate one step at a position with greedy trading.
    Returns (new_coin, new_resources, profit_this_step)
    """
    shop = world[pos]['resources']
    new_resources = dict(resources)
    new_coin = coin

    # Sell resources if shop price >= 60% of global max
    for res, qty in list(new_resources.items()):
        if res in shop and qty > 0:
            gmax = global_prices.get(res, 1)
            local = shop[res]['buy']
            if local >= gmax * 0.6:
                new_coin += qty * local
                new_resources[res] = 0

    # Buy resource with best margin vs global prices
    best = None
    best_margin = 0
    for res, info in shop.items():
        if info['quantity'] <= 0 or info['sell'] <= 0:
            continue
        gmax = global_prices.get(res, 0)
        margin = gmax - info['sell']
        if margin > best_margin:
            best = (res, info['sell'], info['quantity'], margin)
            best_margin = margin

    if best:
        res, price, available, _ = best
        qty = min(available, int(new_coin * 0.9 / price))  # Keep some cash
        if qty > 0:
            new_resources[res] = new_resources.get(res, 0) + qty
            new_coin -= qty * price

    return new_coin, new_resources


def evaluate_state(coin, resources, global_prices):
    """Evaluate total wealth = coin + estimated resource value."""
    total = coin
    for res, qty in resources.items():
        total += qty * global_prices.get(res, 5)
    return total


def get_neighbors_list(world, pos, global_prices):
    """Get best neighbors sorted by opportunity score."""
    neighbors = list(world[pos]['neighbours'].keys())

    def score_neighbor(n):
        shop = world[n]['resources']
        best_margin = 0
        for res, info in shop.items():
            if info['quantity'] > 0:
                margin = global_prices.get(res, 0) - info['sell']
                best_margin = max(best_margin, margin)
        return best_margin

    # Sort by opportunity and limit
    neighbors.sort(key=score_neighbor, reverse=True)
    return neighbors[:MAX_NEIGHBORS]


def generate_paths(world, start_pos, depth, global_prices):
    """Generate movement paths up to given depth."""
    if depth == 0:
        return [[]]

    neighbors = get_neighbors_list(world, start_pos, global_prices)
    if not neighbors:
        return [[start_pos] * depth]

    paths = []
    for first_move in neighbors:
        sub_paths = generate_paths(world, first_move, depth - 1, global_prices)
        for sub_path in sub_paths:
            paths.append([first_move] + sub_path)

    return paths


def find_best_path(world, pos, coin, resources, global_prices, depth):
    """Find the best path by simulating all possibilities."""
    paths = generate_paths(world, pos, depth, global_prices)

    best_path = None
    best_value = -1

    for path in paths:
        # Simulate this path
        sim_coin = coin
        sim_resources = dict(resources)

        for next_pos in path:
            sim_coin, sim_resources = simulate_step(
                world, next_pos, sim_coin, sim_resources, global_prices
            )

        value = evaluate_state(sim_coin, sim_resources, global_prices)
        if value > best_value:
            best_value = value
            best_path = path

    return best_path, best_value


def agent(world_state, *args, **kwargs):
    pos = world_state['you']['position']
    coin = world_state['you']['coin']
    my_resources = world_state['you']['resources']
    world = world_state['world']
    my_shop = world[pos]['resources']

    # Last round - just sell everything
    if u.is_last_round(world_state):
        sells = {r: q for r, q in my_resources.items() if r in my_shop and q > 0}
        return {
            'resources_to_sell_to_shop': sells,
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    global_prices = get_global_prices(world)

    # Find optimal path
    depth = LOOKAHEAD_DEPTH
    best_path, _ = find_best_path(world, pos, coin, my_resources, global_prices, depth)

    if not best_path:
        return {
            'resources_to_sell_to_shop': {},
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    # Execute first step: move to first position in path, then trade
    next_pos = best_path[0]

    # Trade at CURRENT position before moving
    sells = {}
    buys = {}

    # Sell if good price
    for res, qty in my_resources.items():
        if res in my_shop and qty > 0:
            gmax = global_prices.get(res, 1)
            local = my_shop[res]['buy']
            if local >= gmax * 0.6:
                sells[res] = qty
                coin += qty * local

    # Buy best opportunity
    best = None
    best_margin = 0
    for res, info in my_shop.items():
        if info['quantity'] <= 0 or info['sell'] <= 0:
            continue
        gmax = global_prices.get(res, 0)
        margin = gmax - info['sell']
        if margin > best_margin:
            best = (res, info['sell'], info['quantity'])
            best_margin = margin

    if best and best_margin > 0:
        res, price, available = best
        qty = min(available, int(coin * 0.9 / price))
        if qty > 0:
            buys[res] = qty

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': next_pos
    }
