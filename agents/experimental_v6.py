"""
Experimental Agent v6 - Fill the zen→blitz gap.

Current frontier gap:
- zen: $107/r @ 0.0017ms (checks 2 neighbors)
- blitz: $3,547/r @ 0.0075ms (checks ALL neighbors)

Hypothesis: Testing 3-6 neighbors should land between them.
Expected: ~$1,500-2,500/r at ~0.003-0.004ms

This tests the idea across the frontier by varying neighbor count.
"""


def make_zen_variant(max_neighbors):
    """Factory to create zen variants with different neighbor counts."""
    def agent(world_state, *args, **kwargs):
        you = world_state['you']
        pos = you['position']
        coin = you['coin']
        my_res = you['resources']
        world = world_state['world']
        node = world[pos]
        shop = node['resources']

        # Sell everything we have
        sells = {}
        for res, qty in my_res.items():
            if qty > 0 and res in shop:
                sells[res] = qty
                coin += qty * shop[res]['buy']

        neighbors = node['neighbours']
        if not neighbors:
            return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

        # Check up to max_neighbors, pick best arbitrage
        best_dest = None
        best_profit = 0
        best_buys = {}

        count = 0
        for n in neighbors:
            if max_neighbors and count >= max_neighbors:
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
    return agent


# Create variants with different neighbor counts
zen_2 = make_zen_variant(2)    # Current zen
zen_3 = make_zen_variant(3)
zen_4 = make_zen_variant(4)
zen_5 = make_zen_variant(5)
zen_6 = make_zen_variant(6)
zen_8 = make_zen_variant(8)
zen_all = make_zen_variant(None)  # All neighbors (like blitz but simpler)
