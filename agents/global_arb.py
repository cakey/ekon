"""
Global Arbitrage Agent - Uses global price knowledge efficiently.

Strategy:
- Know the best prices globally (cached)
- Buy resources with best global arbitrage margin
- Move toward high-value nodes
"""

import random
from . import utils as u

# Cache global prices per game (reset on round 0)
_best_buy_prices = None  # Best price to sell TO (shops buy from us)
_best_sell_prices = None  # Best price to buy FROM (shops sell to us)


def compute_global_prices(world):
    """Compute best buy/sell prices across all nodes."""
    best_buy = {}  # Max buy price (we sell to shop)
    best_sell = {}  # Min sell price (we buy from shop)

    for node in world.values():
        for res, info in node['resources'].items():
            # Best place to sell (highest buy price)
            if res not in best_buy or info['buy'] > best_buy[res]:
                best_buy[res] = info['buy']
            # Best place to buy (lowest sell price with stock)
            if info['quantity'] > 0 and info['sell'] > 0:
                if res not in best_sell or info['sell'] < best_sell[res]:
                    best_sell[res] = info['sell']

    return best_buy, best_sell


def agent(world_state, *args, **kwargs):
    global _best_buy_prices, _best_sell_prices

    pos = world_state['you']['position']
    coin = world_state['you']['coin']
    my_resources = world_state['you']['resources']
    world = world_state['world']
    my_shop = world[pos]['resources']
    current_round = world_state['meta']['current_round']

    # Reset cache at start of each game (or if not initialized)
    if current_round == 0 or _best_buy_prices is None:
        _best_buy_prices, _best_sell_prices = compute_global_prices(world)

    # Last round - sell everything
    if u.is_last_round(world_state):
        sells = {r: q for r, q in my_resources.items() if r in my_shop and q > 0}
        return {
            'resources_to_sell_to_shop': sells,
            'resources_to_buy_from_shop': {},
            'move': pos
        }

    best_buy = _best_buy_prices
    best_sell = _best_sell_prices

    # Sell everything at >= 70% of global best price
    sells = {}
    for res, qty in my_resources.items():
        if res in my_shop and qty > 0:
            local_buy = my_shop[res]['buy']
            global_best = best_buy.get(res, 1)
            if local_buy >= global_best * 0.7:
                sells[res] = qty
                coin += qty * local_buy

    # Buy resources with best global arbitrage (can sell globally for more)
    buys = {}
    opportunities = []

    for res, info in my_shop.items():
        if info['quantity'] <= 0 or info['sell'] <= 0:
            continue
        local_sell = info['sell']  # What we pay
        global_buy = best_buy.get(res, 0)  # What we can get globally
        if global_buy > local_sell:
            margin = global_buy - local_sell
            ratio = global_buy / local_sell
            opportunities.append((res, local_sell, info['quantity'], ratio))

    # Sort by ratio and buy
    opportunities.sort(key=lambda x: x[3], reverse=True)
    for res, price, available, ratio in opportunities:
        if coin <= 0:
            break
        max_qty = coin / price
        qty = min(max_qty, available)
        if qty > 0:
            buys[res] = qty
            coin -= qty * price

    # Move toward neighbor with best opportunity
    neighbors = list(world[pos]['neighbours'].keys())
    best_neighbor = random.choice(neighbors) if neighbors else pos
    best_score = 0

    for neighbor in neighbors:
        n_shop = world[neighbor]['resources']
        score = 0
        for res, info in n_shop.items():
            if info['quantity'] > 0 and info['sell'] > 0:
                global_buy = best_buy.get(res, 0)
                margin = global_buy - info['sell']
                if margin > 0:
                    score += margin * info['quantity']
        if score > best_score:
            best_score = score
            best_neighbor = neighbor

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': buys,
        'move': best_neighbor
    }
