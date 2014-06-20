shops = False
agent_name = "the_pirate_of_cakey"
other_agents = False
agent_coin = False
agent_position = False
agent_resources = False
agent_move = False
agent_current_shop = False
round_info = False

def print_agent(agent,move,current_shop):
    if agent_name == agent["name"]:
        print "--------------------------------------------"
        print "Agent: " + agent["name"]
        if agent_position:
            print "position: " + str(agent['position'])
        if agent_coin:
            print "Coin: " + str(agent['coin'])
        if agent_resources:
            print "Resources"
            print agent['resources']
        if agent_move:
            print "Move:"
            print move
        if agent_current_shop:
            print "Current Shop: "
            print current_shop

def print_node(shop_node, snode):
    if shops:
        print "NODE: " + str(shop_node)
        print snode

def print_round_start(round_number):
    if round_info:
        print ""
        print "================= Round: " +  str(round_number) + "============================"
        print ""

def print_round_end():
    if round_info:
        print ""
        print "=========================================================================="
        print ""

def print_results(world_agents):
    print "RESULTS!!! :"

    print sorted(
        [(a["name"], a["coin"]) for a in world_agents],
        key = lambda a: a[1], reverse=True)
