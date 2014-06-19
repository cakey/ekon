def profit(info):
    return info["buy"] - info["sell"]

def node_profit(node):
    # nice idea, but we end up selling stuff for a loss,
    # only works because those places have low prices on average
    # return sum([profit(info)*info["quantity"] for name,info in node.items() if profit(info) > 0])
    return sum([profit(info) for name,info in node.items() if profit(info) > 0])

def agent(world_state, *args, **kwargs):

    my_position = world_state['you']['position']
    my_node = world_state['world'][my_position]
    my_neighbours = my_node['neighbours']

    # calculate best node to go to next
    node_profits = [(name, node_profit(info["resources"])) for name, info in world_state['world'].items()]
    destination = sorted(node_profits, key=lambda a: a[1], reverse=True)[0][0]

    # buy/sell at current node

    sells = world_state['you']['resources']

    profits = [(name, profit(info), info) for name, info in my_node["resources"].items() if profit(info) > 0]

    coin_available = world_state['you']['coin']

    buys = {}
    for r in sorted(profits, key=lambda a: a[1], reverse=True):
        max_q_to_buy = coin_available / r[2]["sell"]
        buys[r[0]] = min(max_q_to_buy, r[2]["quantity"] + sells.get(r[0], 0))
        coin_available -= buys[r[0]] * r[2]["sell"]

    return {
        'buy':     sells,
        'sell':    buys,
        'move': destination
    }
