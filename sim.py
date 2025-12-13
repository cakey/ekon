import copy
import logging
import random
import time

import agents
import utils.logger as L

# Log everything, and send it to stderr.
logging.basicConfig(level=logging.DEBUG)

# TODO: JSON config
num_rounds = 200
traveller_start_gold = 10000
resource_prices = [5,25]
starting_quantity = [10,1000]
node_count = 400
edge_ratio = 0.02
resource_names = ["GOLD", "SILVER", "NANOCHIPS", "CAKE", "AZURE_INSTANCES"]
mine_rate = [10,80]

def build_graph(node_count, edge_ratio):

    nodes = range(node_count)

    # create spanning tree
    graph = {nodes[0]:{}}

    chosen_edges = set()

    for node_num in nodes[1:]:
        neighbour = random.choice(list(graph.keys()))
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

        for edge_to_add in random.sample(list(edges_available), k):
            graph[edge_to_add[0]][edge_to_add[1]] = 1
            graph[edge_to_add[1]][edge_to_add[0]] = 1

    return graph

def make_world_shops(world_graph):
    shops = {}
    for shop in world_graph.keys():
        shops[shop] = {
            resource: shop_resource(resource_prices,resource_prices, starting_quantity)
            for resource in random.sample(resource_names, random.randint(1, len(resource_names)))
        }
    return shops

def shop_resource(buyrange, sellrange, quantityrange):
    buy_price = random.randint(*buyrange)
    sell_price = random.randint(max(buy_price, sellrange[0]), sellrange[1])
    return {
        "buy": buy_price,
        "sell": sell_price,
        "quantity": random.randint(*quantityrange)
    }

def run_sim(observer=None, debug_log=False, quiet=False):
    """
    Run the trading simulation.

    Args:
        observer: Optional dict with callbacks:
            - on_round_end(round_num, total_rounds, agents, shops) -> bool
              Returns False to stop simulation early
            - on_agent_action(agent_name, action_type, details)
              Called when agents buy/sell/move
        debug_log: If True, write detailed debug log to file
        quiet: If True, suppress all console output (for visualizer mode)
    """
    # Setup debug logger
    dlog = None
    if debug_log:
        from debug_logger import DebugLogger
        dlog = DebugLogger()

    # Suppress console output in quiet mode
    if quiet:
        logging.getLogger().setLevel(logging.CRITICAL)
        L.quiet = True

    # Here comes the mega function!
    # TODO: refactor ;)

    # setup games

    world_graph = build_graph(node_count, edge_ratio)

    world_shops = make_world_shops(world_graph)

    world_agents = [{
            "name":name,
            "func":func,
            "coin": traveller_start_gold,
            "position": random.choice(list(world_graph.keys())),
            "resources": {},
            "time": 0
        } for name,func in agents.agents.items()]

    if dlog:
        dlog.log_setup(world_graph, world_shops, world_agents)

    # run game

    for round_number in range(num_rounds):
        if dlog:
            dlog.log_round_start(round_number, num_rounds, world_agents)

        L.print_round_start(round_number)
        L.print_nodes(world_shops)

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
                "world": {w: {"neighbours":neighbours, "resources": world_shops[w]} for w,neighbours in world_graph.items()}
            }

            start = time.time()
            move = None
            try:
                move = current_agent["func"](state_to_pass)
            except Exception as e:
                current_agent["time"] += (time.time() - start)
                L.invalid(current_agent, '', e)
                if dlog:
                    dlog.log_agent_exception(current_agent["name"], e)
                continue
            current_agent["time"] += (time.time() - start)

            if dlog:
                dlog.log_agent_turn(current_agent, state_to_pass, move)

            if not isinstance(move, dict):
                L.invalid(current_agent, "Returned move expected to be type dict, actual: %s" % move)
                continue

            current_shop = world_shops[current_agent["position"]]

            # run agent sell commands
            for resource_name, quantity in move.get("resources_to_sell_to_shop", {}).items():
                quantity = int(quantity)
                if quantity < 0:
                    L.invalid(current_agent, "SELL: negative amount?")
                    continue
                if resource_name not in current_shop:
                    L.invalid(current_agent, "SELL: shop does buy resource name %s" % resource_name)
                    continue
                if resource_name not in  current_agent["resources"]:
                    L.invalid(current_agent, "SELL: agent does not have resource name %s" % resource_name)
                    continue
                total_price = quantity * current_shop[resource_name]["buy"]
                if (quantity <= current_agent["resources"].get(resource_name, 0)):
                    current_shop[resource_name]["quantity"] += quantity
                    current_agent["resources"][resource_name] -= quantity
                    current_agent["coin"] += total_price
                    if dlog:
                        dlog.log_transaction(current_agent["name"], "sell", resource_name, quantity, current_shop[resource_name]["buy"], True)
                    if observer and 'on_agent_action' in observer:
                        observer['on_agent_action'](current_agent["name"], "sold", f"{quantity} {resource_name} for ${total_price:,}")
                else:
                    if dlog:
                        dlog.log_transaction(current_agent["name"], "sell", resource_name, quantity, current_shop[resource_name]["buy"], False, "insufficient quantity")
                    L.invalid(current_agent, "SELL: agent does not have sufficient quantity of %s" % resource_name)

            # run agent buy commands
            for resource_name, quantity in move.get("resources_to_buy_from_shop", {}).items():
                quantity = int(quantity)
                if quantity < 0:
                    L.invalid(current_agent, "BUY: negative amount?")
                    continue
                if resource_name not in current_shop:
                    L.invalid(current_agent, "BUY: shop does not have resource name %s" % resource_name)
                    continue
                total_price = quantity * current_shop[resource_name]["sell"]
                if quantity <= current_shop[resource_name]["quantity"]:
                    if current_agent["coin"] >= total_price:
                        current_shop[resource_name]["quantity"] -= quantity
                        if resource_name not in current_agent["resources"]:
                            current_agent["resources"][resource_name] = 0
                        current_agent["resources"][resource_name] += quantity
                        current_agent["coin"] -= total_price
                        if dlog:
                            dlog.log_transaction(current_agent["name"], "buy", resource_name, quantity, current_shop[resource_name]["sell"], True)
                        if observer and 'on_agent_action' in observer:
                            observer['on_agent_action'](current_agent["name"], "bought", f"{quantity} {resource_name} for ${total_price:,}")
                    else:
                        if dlog:
                            dlog.log_transaction(current_agent["name"], "buy", resource_name, quantity, current_shop[resource_name]["sell"], False, "insufficient coin")
                        L.invalid(current_agent, "BUY: insufficient coin to purchase %s" % resource_name)
                else:
                    if dlog:
                        dlog.log_transaction(current_agent["name"], "buy", resource_name, quantity, current_shop[resource_name]["sell"], False, "shop out of stock")
                    L.invalid(current_agent, "BUY: insufficient quantity in shop, resource: %s" % resource_name)

            L.print_agent(current_agent, move, current_shop)

            # move agent
            if move.get("move", None) is not None:
                if (move["move"] in world_graph[current_agent["position"]].keys() or
                    move["move"] == current_agent["position"]):
                    old_pos = current_agent["position"]
                    current_agent["position"] = move["move"]
                    if dlog and old_pos != move["move"]:
                        dlog.log_movement(current_agent["name"], old_pos, move["move"], True)
                    if observer and 'on_agent_action' in observer and old_pos != move["move"]:
                        observer['on_agent_action'](current_agent["name"], "moved", f"to node {move['move']}")
                else:
                    if dlog:
                        dlog.log_movement(current_agent["name"], current_agent["position"], move["move"], False, "invalid destination")
                    L.invalid(current_agent, "Invalid Location to move to: %s" % move["move"])


        L.print_round_end()

        if dlog:
            dlog.log_round_end(world_agents)

        # Call observer at end of round
        if observer and 'on_round_end' in observer:
            if not observer['on_round_end'](round_number, num_rounds, world_agents, world_shops):
                break  # Observer requested stop

    # display winner

    if dlog:
        dlog.log_final_results(world_agents)
        dlog.close()

    L.print_results(world_agents)


if __name__ == '__main__':
    run_sim()

