import logging

# Log everything, and send it to stderr.
logging.basicConfig(level=logging.DEBUG)

shops = False
agent_name = ""
other_agents = False
agent_coin = False
agent_position = False
agent_resources = False
agent_move = False
agent_current_shop = False
round_info = False
time_logging = False

def print_agent(agent,move,current_shop):
    if agent_name == agent["name"] or other_agents:
        print("--------------------------------------------")
        print("Agent: " + agent["name"])
        if agent_position:
            print("position: " + str(agent['position']))
        if agent_coin:
            print("Coin: " + str(agent['coin']))
        if agent_resources:
            print("Resources")
            print(agent['resources'])
        if agent_move:
            print("Move:")
            print(move)
        if agent_current_shop:
            print("Current Shop: ")
            print(current_shop)

def invalid(agent, message='', exc=None):
    if agent_name == agent["name"] or other_agents:
        if message:
            print("Invalid Move(%s): %s" % (agent['name'], message))
        if exc is not None:
            print("Exception thrown by %s! :" % agent['name'])
            logging.exception(exc)



def print_node(shop_node, snode):
    if shops:
        print("NODE: " + str(shop_node))
        print(snode)

def print_nodes(world_shops):
    if shops:
        for shop_nodes,node in world_shops.items():
            print_node(shop_nodes,node)
        print("")


def print_round_start(round_number):
    if round_info:
        print("")
        print("================= Round: " +  str(round_number) + "============================")
        print("")

def print_round_end():
    if round_info:
        print("")
        print("==========================================================================")
        print("")

def print_results(world_agents):
    print("=================== RESULTS!!! ===================")

    print("Final Coin")
    print(sorted(
        [(a["name"], a["coin"]) for a in world_agents],
        key = lambda a: a[1], reverse=True))

    if time_logging:
        print("Time spent")
        print(sorted(
            [(a["name"], "%.5f" % a["time"]) for a in world_agents],
            key = lambda a: a[1]))
