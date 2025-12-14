#!/usr/bin/env python3
"""
Test individual agents for bugs and edge cases.

Usage:
    python test_agent.py                    # Test all agents
    python test_agent.py ultrafast          # Test specific agent
    python test_agent.py --stress 100       # Run 100 stress test rounds
"""

import argparse
import random
import traceback
import sys

# Create a mock world state for testing
def create_mock_world_state(num_nodes=10, current_round=50, total_rounds=200):
    """Create a minimal valid world state for testing."""
    resources = ["GOLD", "SILVER", "NANOCHIPS", "CAKE", "AZURE_INSTANCES"]

    # Build graph
    world = {}
    for i in range(num_nodes):
        neighbors = {}
        # Connect to 2-4 random other nodes
        for j in random.sample(range(num_nodes), min(4, num_nodes)):
            if j != i:
                neighbors[j] = 1

        # Create shop with random resources
        shop = {}
        for res in random.sample(resources, random.randint(1, len(resources))):
            buy = random.randint(5, 25)
            sell = random.randint(buy, 25)
            shop[res] = {
                'buy': buy,
                'sell': sell,
                'quantity': random.randint(10, 1000)
            }

        world[i] = {
            'neighbours': neighbors,
            'resources': shop
        }

    # Ensure connectivity
    for i in range(num_nodes):
        if not world[i]['neighbours']:
            j = (i + 1) % num_nodes
            world[i]['neighbours'][j] = 1
            world[j]['neighbours'][i] = 1

    pos = random.randint(0, num_nodes - 1)

    return {
        'you': {
            'coin': random.randint(1000, 50000),
            'position': pos,
            'resources': {random.choice(resources): random.randint(0, 100) for _ in range(random.randint(0, 3))}
        },
        'meta': {
            'current_round': current_round,
            'total_rounds': total_rounds
        },
        'world': world
    }


def validate_move(move, world_state):
    """Validate an agent's move. Returns (is_valid, errors)."""
    errors = []

    if not isinstance(move, dict):
        return False, [f"Move must be dict, got {type(move).__name__}"]

    required_keys = ['resources_to_sell_to_shop', 'resources_to_buy_from_shop', 'move']
    for key in required_keys:
        if key not in move:
            errors.append(f"Missing required key: {key}")

    if errors:
        return False, errors

    pos = world_state['you']['position']
    world = world_state['world']
    shop = world[pos]['resources']
    coin = world_state['you']['coin']
    my_resources = world_state['you']['resources']

    # Validate sells
    sells = move.get('resources_to_sell_to_shop', {})
    if not isinstance(sells, dict):
        errors.append(f"sells must be dict, got {type(sells).__name__}")
    else:
        for res, qty in sells.items():
            if res not in shop:
                errors.append(f"Can't sell {res}: shop doesn't buy it")
            if res not in my_resources or my_resources[res] < qty:
                errors.append(f"Can't sell {qty} {res}: don't have enough")
            if qty < 0:
                errors.append(f"Can't sell negative quantity of {res}")
            else:
                coin += qty * shop.get(res, {}).get('buy', 0)

    # Validate buys
    buys = move.get('resources_to_buy_from_shop', {})
    if not isinstance(buys, dict):
        errors.append(f"buys must be dict, got {type(buys).__name__}")
    else:
        for res, qty in buys.items():
            if res not in shop:
                errors.append(f"Can't buy {res}: shop doesn't have it")
            elif shop[res]['quantity'] < qty:
                errors.append(f"Can't buy {qty} {res}: shop only has {shop[res]['quantity']}")
            elif shop[res]['sell'] * int(qty) > coin:
                errors.append(f"Can't buy {qty} {res}: costs ${shop[res]['sell'] * int(qty)}, have ${coin}")
            if qty < 0:
                errors.append(f"Can't buy negative quantity of {res}")

    # Validate move
    dest = move.get('move')
    if dest is not None:
        if dest != pos and dest not in world[pos]['neighbours']:
            errors.append(f"Can't move to {dest}: not a neighbor of {pos}")

    return len(errors) == 0, errors


def test_agent(agent_name, agent_func, num_tests=20, verbose=True):
    """Test an agent with various scenarios."""
    passed = 0
    failed = 0
    errors_found = []

    # Test scenarios
    scenarios = [
        ("Normal game", lambda: create_mock_world_state()),
        ("Early game", lambda: create_mock_world_state(current_round=0)),
        ("Last round", lambda: create_mock_world_state(current_round=199, total_rounds=200)),
        ("Small world", lambda: create_mock_world_state(num_nodes=3)),
        ("Large world", lambda: create_mock_world_state(num_nodes=50)),
        ("Low coin", lambda: {**create_mock_world_state(), 'you': {**create_mock_world_state()['you'], 'coin': 10}}),
        ("No resources", lambda: {**create_mock_world_state(), 'you': {**create_mock_world_state()['you'], 'resources': {}}}),
    ]

    for scenario_name, create_state in scenarios:
        for i in range(num_tests // len(scenarios) + 1):
            try:
                world_state = create_state()
                move = agent_func(world_state)
                valid, errs = validate_move(move, world_state)

                if valid:
                    passed += 1
                else:
                    failed += 1
                    errors_found.append((scenario_name, errs, world_state, move))

            except Exception as e:
                failed += 1
                errors_found.append((scenario_name, [f"Exception: {e}"], None, traceback.format_exc()))

    if verbose:
        print(f"\n{agent_name}:")
        print(f"  Passed: {passed}, Failed: {failed}")

        if errors_found:
            print(f"  Errors found:")
            for scenario, errs, state, move in errors_found[:3]:
                print(f"    [{scenario}]")
                for e in errs[:3]:
                    print(f"      - {e}")

    return passed, failed, errors_found


def main():
    parser = argparse.ArgumentParser(description='Test trading agents')
    parser.add_argument('agent', nargs='?', help='Specific agent to test')
    parser.add_argument('--stress', type=int, default=20, help='Number of test iterations')
    args = parser.parse_args()

    import agents as agents_module

    print("Agent Testing")
    print("=" * 60)

    total_passed = 0
    total_failed = 0

    agents_to_test = {args.agent: agents_module.agents[args.agent]} if args.agent else agents_module.agents

    for name, func in agents_to_test.items():
        passed, failed, errors = test_agent(name, func, num_tests=args.stress)
        total_passed += passed
        total_failed += failed

    print("\n" + "=" * 60)
    print(f"Total: {total_passed} passed, {total_failed} failed")

    return 0 if total_failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
