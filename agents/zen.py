"""
Zen Agent - Minimal profitable agent to dominate matt_shitty_agent.

Matt loses money (-$49/r @ 0.0017ms) by buying random stuff and never selling.
Zen aims to be faster AND profitable by doing minimal work:
1. Sell any resources we're holding (at current shop)
2. Pick first neighbor, check for any arbitrage
3. Buy first profitable resource, move there

No loops over all neighbors, no sorting, no optimization - just fast profit.
"""


def agent(world_state, *args, **kwargs):
    you = world_state['you']
    pos = you['position']
    coin = you['coin']
    my_res = you['resources']
    world = world_state['world']
    node = world[pos]
    shop = node['resources']

    # Sell everything we have (simple, fast)
    sells = {}
    for res, qty in my_res.items():
        if qty > 0 and res in shop:
            sells[res] = qty
            coin += qty * shop[res]['buy']

    # Get neighbors
    neighbors = node['neighbours']
    if not neighbors:
        return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

    # Check first 2 neighbors, pick best total arbitrage
    best_dest = None
    best_profit = 0
    best_buys = {}

    count = 0
    for n in neighbors:
        if count >= 2:
            break
        count += 1

        n_shop = world[n]['resources']
        profit = 0
        buys = {}
        budget = coin

        for res, info in shop.items():
            if budget <= 0:
                break
            if info['quantity'] > 0 and info['sell'] > 0:
                n_info = n_shop.get(res)
                if n_info and n_info['buy'] > info['sell']:
                    amt = min(budget // info['sell'], info['quantity'])
                    if amt > 0:
                        buys[res] = amt
                        budget -= amt * info['sell']
                        profit += (n_info['buy'] - info['sell']) * amt

        if profit > best_profit:
            best_profit = profit
            best_dest = n
            best_buys = buys

    if not best_dest:
        best_dest = next(iter(neighbors))
        best_buys = {}

    return {
        'resources_to_sell_to_shop': sells,
        'resources_to_buy_from_shop': best_buys,
        'move': best_dest
    }
