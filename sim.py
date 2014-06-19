import copy
import logging
import random

import agents

# Log everything, and send it to stderr.
logging.basicConfig(level=logging.DEBUG)


def build_graph(node_count):

    graph = {}

    for node_num in range(node_count):
        graph[node_num] = {n:1 for n in range(node_count) if n != node_num} 

    return graph


def run_sim():

    # setup games

    num_rounds = 10
    traveller_start_gold = 10000
    resource_prices = [5,15]
    starting_quantity = [10,1000]
    node_count = 10

    world_graph = build_graph(node_count)

    resource_names = ["GOLD", "SILVER", "NANOCHIPS"]

    world_shops = {
        shop: {
            resource: {
                "buy": random.randint(*resource_prices),
                "sell": random.randint(*resource_prices),
                "quantity": random.randint(*starting_quantity)
            } for resource in resource_names }
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
        print "round number: %s" % round_number
        print "world agents: %s" % world_agents
        for current_agent in world_agents:
            print "agent to play: %s" % current_agent["name"]
            state_to_pass = {
                "you": {
                    "coin":current_agent["coin"],
                    "position":current_agent["position"],
                    "resources": copy.deepcopy(current_agent["resources"])
                },
                "world": {w: {"neighbours":neighbours, "resources": world_shops[w]} for w,neighbours in world_graph.iteritems()}
            }

            try:
                move = current_agent["func"](state_to_pass)
            except Exception as e:
                print "Exception thrown by %s!" % current_agent['name']
                logging.exception(e)
            print move

            if not isinstance(move, dict):
                print "move not dict"
                continue

            current_shop = world_shops[current_agent["position"]]
            print "current_shop: %s" % current_shop

            # run agent sell commands
            for resource_name, quantity in move.get("buy", {}).iteritems():
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

            # move agent
            if move.get("move", None) is not None:
                if move["move"] in world_graph[current_agent["position"]].keys():
                    current_agent["position"] = move["move"]

                else:
                    print "INVALID LOCATION"

    # display winner

    print "RESULTS!!! :"

    print sorted(
        [(a["name"], a["coin"]) for a in world_agents],
        key = lambda a: a[1], reverse=True)

if __name__ == '__main__':
    run_sim()
