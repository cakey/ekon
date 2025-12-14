"""
Experimental Agent v8 - Zen variants with NAS (Neighbor-Aware Selling)

Hypothesis: NAS helped blitz (+$212, no time cost). Zen variants have
similar structure, should benefit similarly.

Prediction: Each zen variant gains $100-300/r with minimal time increase.
"""


def make_zen_nas_variant(max_neighbors):
    """Factory to create zen+NAS variants with different neighbor counts."""
    def agent(world_state, *args, **kwargs):
        you = world_state['you']
        pos = you['position']
        coin = you['coin']
        my_res = you['resources']
        world = world_state['world']
        node = world[pos]
        shop = node['resources']

        neighbors = node['neighbours']
        if not neighbors:
            # No neighbors - just sell everything
            sells = {res: qty for res, qty in my_res.items() if qty > 0 and res in shop}
            return {'resources_to_sell_to_shop': sells, 'resources_to_buy_from_shop': {}, 'move': pos}

        # First find best neighbor (need this for NAS decision)
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
            budget = coin  # Use original coin for evaluation

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

        # NAS: Only sell if destination doesn't pay more
        dest_shop = world[best_dest]['resources']
        sells = {}
        for res, qty in my_res.items():
            if qty > 0 and res in shop:
                current_price = shop[res]['buy']
                dest_info = dest_shop.get(res)
                dest_price = dest_info['buy'] if dest_info else 0
                if current_price >= dest_price:
                    sells[res] = qty
                    coin += qty * current_price

        # Recalculate buys with updated coin (after selling)
        if best_buys:
            n_shop = world[best_dest]['resources']
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
            best_buys = buys

        return {
            'resources_to_sell_to_shop': sells,
            'resources_to_buy_from_shop': best_buys,
            'move': best_dest
        }
    return agent


# Create NAS variants
zen_nas_2 = make_zen_nas_variant(2)
zen_nas_3 = make_zen_nas_variant(3)
zen_nas_4 = make_zen_nas_variant(4)
zen_nas_5 = make_zen_nas_variant(5)
zen_nas_6 = make_zen_nas_variant(6)
zen_nas_8 = make_zen_nas_variant(8)
zen_nas_all = make_zen_nas_variant(None)
