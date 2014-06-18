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
            "coin": 1000,
            "location": random.choice(world_graph.keys())
        } for name,func in agents.agents.iteritems()]

    print world_graph
    print world_shops
    print world_agents

    print "everyone loses"

if __name__ == '__main__':
    run_sim()
