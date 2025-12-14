#!/usr/bin/env python3
"""
Experiment runner - compare agent variants.

Usage:
    python3 experiment.py [num_runs]

To test new variants, modify the `variants` list in main().
Results should be recorded in EXPERIMENTS.md.
"""

import copy
import random
import time
import sys

# Simulation parameters (must match sim.py)
NUM_ROUNDS = 200
STARTING_COIN = 10000
RESOURCE_PRICES = [5, 25]
STARTING_QUANTITY = [10, 1000]
NODE_COUNT = 400
EDGE_RATIO = 0.02
RESOURCE_NAMES = ["GOLD", "SILVER", "NANOCHIPS", "CAKE", "AZURE_INSTANCES"]


def build_graph(node_count, edge_ratio):
    nodes = range(node_count)
    graph = {nodes[0]: {}}
    chosen_edges = set()

    for node_num in nodes[1:]:
        neighbour = random.choice(list(graph.keys()))
        graph[node_num] = {neighbour: 1}
        graph[neighbour][node_num] = 1
        chosen_edges.add((neighbour, node_num))

    edges_available = set()
    for i, node_a in enumerate(nodes):
        for node_b in nodes[(i + 1):]:
            edges_available.add((node_a, node_b))

    edges_available -= chosen_edges
    k = min(len(edges_available), int(edge_ratio * len(edges_available) + len(chosen_edges)))

    if k > len(chosen_edges):
        for edge_to_add in random.sample(list(edges_available), k):
            graph[edge_to_add[0]][edge_to_add[1]] = 1
            graph[edge_to_add[1]][edge_to_add[0]] = 1

    return graph


def make_world_shops(world_graph):
    shops = {}
    for shop in world_graph.keys():
        shops[shop] = {
            resource: {
                "buy": random.randint(*RESOURCE_PRICES),
                "sell": random.randint(*RESOURCE_PRICES),
                "quantity": random.randint(*STARTING_QUANTITY)
            }
            for resource in random.sample(RESOURCE_NAMES, random.randint(1, len(RESOURCE_NAMES)))
        }
        for res, info in shops[shop].items():
            if info['sell'] < info['buy']:
                info['sell'] = info['buy']
    return shops


def run_single_agent(agent_func, seed=None):
    """Run a single agent through a full simulation."""
    if seed is not None:
        random.seed(seed)

    world_graph = build_graph(NODE_COUNT, EDGE_RATIO)
    world_shops = make_world_shops(world_graph)

    agent_state = {
        "coin": STARTING_COIN,
        "position": random.choice(list(world_graph.keys())),
        "resources": {},
        "time": 0
    }

    for round_number in range(NUM_ROUNDS):
        state_to_pass = {
            "you": {
                "coin": agent_state["coin"],
                "position": agent_state["position"],
                "resources": copy.deepcopy(agent_state["resources"])
            },
            "meta": {
                "current_round": round_number,
                "total_rounds": NUM_ROUNDS
            },
            "world": {w: {"neighbours": neighbours, "resources": world_shops[w]}
                      for w, neighbours in world_graph.items()}
        }

        start = time.perf_counter()
        try:
            move = agent_func(state_to_pass)
        except Exception as e:
            print(f"Agent error: {e}")
            continue
        agent_state["time"] += (time.perf_counter() - start)

        if not isinstance(move, dict):
            continue

        current_shop = world_shops[agent_state["position"]]

        # Process sells
        for resource_name, quantity in move.get("resources_to_sell_to_shop", {}).items():
            quantity = int(quantity)
            if quantity <= 0 or resource_name not in current_shop:
                continue
            if resource_name not in agent_state["resources"]:
                continue
            if quantity <= agent_state["resources"].get(resource_name, 0):
                current_shop[resource_name]["quantity"] += quantity
                agent_state["resources"][resource_name] -= quantity
                agent_state["coin"] += quantity * current_shop[resource_name]["buy"]

        # Process buys
        for resource_name, quantity in move.get("resources_to_buy_from_shop", {}).items():
            quantity = int(quantity)
            if quantity <= 0 or resource_name not in current_shop:
                continue
            total_price = quantity * current_shop[resource_name]["sell"]
            if quantity <= current_shop[resource_name]["quantity"]:
                if agent_state["coin"] >= total_price:
                    current_shop[resource_name]["quantity"] -= quantity
                    if resource_name not in agent_state["resources"]:
                        agent_state["resources"][resource_name] = 0
                    agent_state["resources"][resource_name] += quantity
                    agent_state["coin"] -= total_price

        # Process move
        if move.get("move") is not None:
            if (move["move"] in world_graph[agent_state["position"]].keys() or
                    move["move"] == agent_state["position"]):
                agent_state["position"] = move["move"]

    return agent_state["coin"], agent_state["time"] * 1000


def run_experiment(agent_func, name, num_runs=20, seeds=None):
    """Run multiple simulations and collect stats."""
    coins = []
    times = []

    for i in range(num_runs):
        seed = seeds[i] if seeds else None
        coin, time_ms = run_single_agent(agent_func, seed)
        coins.append(coin)
        times.append(time_ms)

    avg_coin = sum(coins) / len(coins)
    avg_time = sum(times) / len(times)
    profit = avg_coin - STARTING_COIN
    ppr = profit / NUM_ROUNDS
    tpr = avg_time / NUM_ROUNDS
    efficiency = ppr / tpr if tpr > 0.0001 else ppr * 10000

    return {
        "name": name,
        "avg_coin": avg_coin,
        "profit": profit,
        "ppr": ppr,
        "tpr": tpr,
        "efficiency": efficiency
    }


def main():
    # Import agents to compare
    from agents import champion_v1, champion_v2, champion_v3, blitz, lookahead
    from agents import experimental_v4 as v4

    # ==========================================================================
    # PARETO FRONTIER AGENTS - always include these as baselines
    # See EXPERIMENTS.md "Experimental Methodology" for validation rules
    # Updated after Iteration 5: blitz+nas, v2+nas now on frontier
    # ==========================================================================
    from agents import champion_v5, champion_v5_blitz
    frontier = [
        (champion_v5_blitz.agent, "blitz+nas"),  # fastest (replaces blitz)
        (champion_v1.agent, "v1"),                # balanced-fast
        (champion_v5.agent, "v2+nas"),            # balanced (BEST - dominates v2)
        (champion_v3.agent, "v3"),                # max profit
    ]

    # ==========================================================================
    # EXPERIMENTAL AGENTS - add new agents here to test against frontier
    # After testing: if dominated by any frontier agent, remove it
    #
    # Original agents tested - all dominated by blitz:
    #   pirate_of_cakey: $3,485/r @ 0.009ms (blitz: $3,588/r @ 0.007ms)
    #   east_india: $813/r @ 0.027ms
    #   rockeffeler: $300/r @ 0.015ms
    # ==========================================================================
    experimental = [
        # Add new experimental agents here
    ]

    variants = frontier + experimental

    num_runs = 30
    if len(sys.argv) > 1:
        num_runs = int(sys.argv[1])

    seeds = [random.randint(0, 1000000) for _ in range(num_runs)]

    print(f"Running {num_runs} simulations per variant...\n")
    print("=" * 80)
    print(f"{'Variant':<20} {'$/round':>10} {'ms/round':>10} {'Efficiency':>12} {'Δ$/r':>10}")
    print("=" * 80)

    results = []
    baseline_result = None

    for agent_func, name in variants:
        result = run_experiment(agent_func, name, num_runs, seeds)
        results.append(result)

        if baseline_result is None:
            baseline_result = result
            delta = "-"
        else:
            delta = f"{result['ppr'] - baseline_result['ppr']:+.1f}"

        print(f"{name:<20} {result['ppr']:>+10.1f} {result['tpr']:>10.4f} {result['efficiency']:>12.1f} {delta:>10}")

    print("=" * 80)

    # Pareto dominance check
    print("\n--- Pareto Frontier Analysis ---")

    # Check each agent for dominance
    frontier_agents = []
    dominated_agents = []

    for i, r in enumerate(results):
        dominated_by = None
        for j, other in enumerate(results):
            if i == j:
                continue
            # other dominates r if: other has >= profit AND <= time (with at least one strict)
            if other['ppr'] >= r['ppr'] and other['tpr'] <= r['tpr']:
                if other['ppr'] > r['ppr'] or other['tpr'] < r['tpr']:
                    dominated_by = other['name']
                    break

        if dominated_by:
            dominated_agents.append((r['name'], dominated_by))
        else:
            frontier_agents.append(r['name'])

    print(f"Frontier: {', '.join(frontier_agents)}")
    if dominated_agents:
        print("Dominated (should discard):")
        for agent, dominator in dominated_agents:
            print(f"  - {agent} dominated by {dominator}")
    else:
        print("No dominated agents.")

    print("\nRecord results in EXPERIMENTS.md")


if __name__ == "__main__":
    main()
