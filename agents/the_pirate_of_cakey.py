import random

import utils as u

def profit(info):
    return info["buy"] - info["sell"]


def node_profit(node):
    """ profit for a single node """
    # nice idea, but we end up selling stuff for a loss,
    # only works because those places have low prices on average
    # return sum([profit(info)*info["quantity"] for name,info in node.items() if profit(info) > 0])
    return sum([profit(info) for name,info in node.items() if profit(info) > 0])

def potential_profit(from_shop_r, to_shop_r):

    profit = 0
    for resource, info in from_shop_r.items():
        sell_price = info["sell"]
        buy_price = to_shop_r.get(resource, {}).get("buy", 0)
        if sell_price < buy_price:
            profit += (buy_price-sell_price) * info["quantity"]

    return profit

def profitable_resources(from_shop_r, to_shop_r):
    profitable = {}
    for resource, info in from_shop_r.items():
        sell_price = info["sell"]
        buy_price = to_shop_r.get(resource, {}).get("buy", 0)
        if sell_price < buy_price:
            profitable[resource] = (buy_price/sell_price)

    print len(profitable)

    return sorted(profitable.items(), reverse=True, key=lambda a: a[1])

def neighbour_profit(world_state, node_label=None):
    """
        if we just bought all the resources at the current node and then sold them on,
        what is the maximum profit we could make?
    """
    if node_label is None:
        node_label = world_state["you"]["position"]

    current_node = world_state["world"][node_label]
    current_resources = current_node["resources"]

    best_label = None
    highest_profit = 0

    for neighbour in u.neighbours(world_state, node_label):
        neighbour_resources = world_state["world"][neighbour]["resources"]
        p = potential_profit(current_resources, neighbour_resources)
        if p > highest_profit:
            highest_profit = p
            best_label = neighbour
        
    return (best_label, highest_profit)


def agent(world_state, *args, **kwargs):

    my_position = world_state['you']['position']
    my_node = world_state['world'][my_position]

    (next_node, _) = neighbour_profit(world_state)

    print next_node

    if next_node is None:
        # want to check neighbour profit recursively,
        # but for now pick a neighbour at random...
        next_node = random.choice(u.neighbours(world_state))

    ### sell

    # sell everything (we can always rebuy)
    sells = world_state['you']['resources']

    ### buy

    # buy as many resources that profit on the next node as possible

    profitable = profitable_resources(my_node["resources"], world_state['world'][next_node]["resources"])

    print profitable

    coin_available = world_state['you']['coin']    
    buys = {}
  
    for (name, profit) in profitable:
        max_q_to_buy = coin_available / my_node["resources"][name]["sell"]
        buys[name] = min(max_q_to_buy, my_node["resources"][name]["quantity"] + sells.get(name, 0))
        coin_available -= buys[name] * my_node["resources"][name]["sell"]

    return {
        'buy':     sells,
        'sell':    buys,
        'move': next_node
    }
