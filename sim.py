import copy
import logging
import random

import utils.logger as L
import agents

# Log everything, and send it to stderr.
logging.basicConfig(level=logging.DEBUG)


def build_graph(node_count, edge_ratio):

    nodes = range(node_count)

    # create spanning tree
    graph = {nodes[0]:{}}

    chosen_edges = set()

    for node_num in nodes[1:]:
        neighbour = random.choice(graph.keys())
        graph[node_num] = {neighbour: 1}
        graph[neighbour][node_num] = 1
        chosen_edges.add((neighbour, node_num))


    edges_available = set()
    # add all possible edges

    for i, node_a in enumerate(nodes):
        for node_b in nodes[(i+1):]:
            edges_available.add((node_a, node_b))

    edges_available -= chosen_edges

    # add as many edges as needed:
    k = min(len(edges_available), int(edge_ratio * len(edges_available)+len(chosen_edges)))

    if k > len(chosen_edges):

        for edge_to_add in random.sample(edges_available, k):
            graph[edge_to_add[0]][edge_to_add[1]] = 1
            graph[edge_to_add[1]][edge_to_add[0]] = 1

    return graph

def shop_resource(buyrange, sellrange, quantityrange):
    buy_price = random.randint(*buyrange)
    sell_price = random.randint(max(buy_price, sellrange[0]), sellrange[1])
    return {
        "buy": buy_price,
        "sell": sell_price,
        "quantity": random.randint(*quantityrange)
    }

def run_sim():

    # setup games

    num_rounds = 20
    traveller_start_gold = 10000
    resource_prices = [5,25]
    starting_quantity = [10,1000]
    node_count = 40
    edge_ratio = 0.25

    world_graph = build_graph(node_count, edge_ratio)

    resource_names = ["GOLD", "SILVER", "NANOCHIPS", "CAKE", "AZURE_INSTANCES"]

    world_shops = {
        shop: {
            resource: shop_resource(resource_prices,resource_prices, starting_quantity)
            for resource in random.sample(resource_names, random.randint(1, len(resource_names))) }
        for shop in world_graph.keys()}

    world_agents = [{
            "name":name,
            "func":func,
            "coin": traveller_start_gold,
            "position": random.choice(world_graph.keys()),
            "resources": {}
        } for name,func in agents.agents.iteritems()]

    # run game

    for round_number in range(num_rounds):

        L.print_round_start(round_number)

        for shop_nodes,node in world_shops.items():
            L.print_node(shop_nodes,node)
        print ""

        random.shuffle(world_agents)

        for current_agent in world_agents:
            state_to_pass = {
                "you": {
                    "coin":current_agent["coin"],
                    "position":current_agent["position"],
                    "resources": copy.deepcopy(current_agent["resources"])
                },
                "meta": {
                    "current_round" : round_number,
                    "total_rounds" : num_rounds
                },
                "world": {w: {"neighbours":neighbours, "resources": world_shops[w]} for w,neighbours in world_graph.iteritems()}
            }

            try:
                move = current_agent["func"](state_to_pass)
            except Exception as e:
                print "Exception thrown by %s!" % current_agent['name']
                logging.exception(e)
            #print move

            if not isinstance(move, dict):
                print "move not dict"
                continue

            current_shop = world_shops[current_agent["position"]]
            


            # run agent sell commands
            for resource_name, quantity in move.get("buy", {}).iteritems():
                quantity = int(quantity)
                if quantity < 0:
                    print "SELL: negative amount?"
                    continue
                if resource_name not in current_shop:
                    print "BUY: shop does not have resource name %s " % resource_name
                    continue
                total_price = quantity * current_shop[resource_name]["buy"]
                if (quantity <= current_agent["resources"].get(resource_name, 0)):
                    current_shop[resource_name]["quantity"] += quantity
                    current_agent["resources"][resource_name] -= quantity
                    current_agent["coin"] += total_price
                else:
                    print "SELL: insufficient quantity"

            # run agent buy commands
            for resource_name, quantity in move.get("sell", {}).iteritems():
                quantity = int(quantity)
                if quantity < 0:
                    print "BUY: negative amount?"
                    continue
                if resource_name not in current_shop:
                    print "BUY: shop does not have resource name %s " % resource_name
                    continue
                total_price = quantity * current_shop[resource_name]["sell"]
                if quantity <= current_shop[resource_name]["quantity"]:

                    if current_agent["coin"] >= total_price:
                        current_shop[resource_name]["quantity"] -= quantity
                        if resource_name not in current_agent["resources"]:
                            current_agent["resources"][resource_name] = 0
                        current_agent["resources"][resource_name] += quantity
                        current_agent["coin"] -= total_price
                    else:
                        print "BUY: insufficient coin, resource: %s " % resource_name
                else:
                    print "BUY: insufficient quantity in shop, resource: %s " % resource_name

            L.print_agent(current_agent, move, current_shop)

            # move agent
            if move.get("move", None) is not None:
                if (move["move"] in world_graph[current_agent["position"]].keys() or
                    move["move"] == current_agent["position"]):
                    current_agent["position"] = move["move"]

                else:
                    print "INVALID LOCATION"

    L.print_round_end()

    # display winner

    L.print_results(world_agents)


if __name__ == '__main__':
    run_sim()

