import copy
import random

import agents



def build_graph(node_count):

    graph = {}

    for node_num in range(node_count):
        graph[node_num] = {n:1 for n in range(node_count) if n != node_num} 

    return graph


def run_sim():
    num_rounds = 100
    traveller_start_gold = 1000
    resource_price = [5,15]
    resource_count = 5
    node_count = 10

    world_graph = build_graph(node_count)
    world_shops = {
        name: {
            "GOLD": {
                "buy": random.randint(10,100),
                "sell": random.randint(10,100),
                "quantity": random.randint(10,100)
            },
            "SILVER": {
                "buy": random.randint(10,100),
                "sell": random.randint(10,100),
                "quantity": random.randint(10,100)
            },
            "NANOCHIPS": {
                "buy": random.randint(10,100),
                "sell": random.randint(10,100),
                "quantity": random.randint(10,100)
            }
        } for name in world_graph.keys()}

    world_agents = [{
            "name":name,
            "func":func,
            "coin": traveller_start_gold,
            "position": random.choice(world_graph.keys()),
            "resources": {}
        } for name,func in agents.agents.iteritems()]

    for round_number in range(num_rounds):
        print "round number: %s" % round_number
        print world_agents
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

            move = current_agent["func"](state_to_pass)
            print move

            if not isinstance(move, dict):
                print "move not dict"
                continue

            current_shop = world_shops[current_agent["position"]]

            # run agent sell commands
            for resource_name, quantity in move.get("sell", {}).iteritems():
                total_price = quantity * current_shop["resource_name"]["sell"]
                if (quantity >= current_agent["resources"]["resource_name"]):
                    current_shop["resource_name"]["quantity"] += quantity
                    current_agent["resources"][resource_name] -= quantity
                    current_agent["coin"] += total_price
                else:
                    print "SELL: insufficient quantity"

            # run agent buy commands
            for resource_name, quantity in move.get("buy", {}).iteritems():
                total_price = quantity * current_shop["resource_name"]["buy"]
                if (quantity >= current_shop["resource_name"]["quantity"] and 
                    current_agent["coin"] >= total_price):
                    current_shop["resource_name"]["quantity"] -= quantity
                    if resource_name not in current_agent["resources"]:
                        current_agent["resources"][resource_name] = 0
                    current_agent["resources"][resource_name] += quantity
                    current_agent["coin"] -= total_price
                else:
                    print "BUY: insufficient funds or quantity in shop"

            # move agent
            if move.get("move", None) is not None:
                if move["move"] in world_graph[current_agent["position"]].keys():
                    current_agent["position"] = move["move"]

                else:
                    print "INVALID LOCATION"

    print world_graph
    print world_shops
    print world_agents

    print "everyone loses"

if __name__ == '__main__':
    run_sim()
