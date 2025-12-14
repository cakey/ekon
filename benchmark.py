#!/usr/bin/env python3
"""
Fast benchmarking script for testing agent improvements.

Usage:
    python benchmark.py                    # Run 10 sims, 200 rounds
    python benchmark.py -n 50              # Run 50 sims
    python benchmark.py -r 50              # Only 50 rounds per sim (faster)
    python benchmark.py -n 20 -r 100       # 20 sims, 100 rounds each
    python benchmark.py -j 4               # Use 4 parallel workers
    python benchmark.py --only fast_lookahead,the_pirate_of_cakey  # Test specific agents
    python benchmark.py --watch            # Auto-rerun when agent files change
"""

import argparse
import glob
import importlib
import os
import time
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor, as_completed
import sys

# Must import these at module level for multiprocessing
STARTING_COIN = 10000


def calc_efficiency(ppr, tpr_ms):
    if tpr_ms <= 0.001:
        return ppr * 1000
    return ppr / tpr_ms


def run_single_sim(args):
    """Run a single simulation. Designed for multiprocessing."""
    sim_id, num_rounds, agent_filter = args

    # Import inside function for multiprocessing
    import sim
    import agents as agents_module
    import traceback

    # Patch the number of rounds
    original_rounds = sim.num_rounds
    sim.num_rounds = num_rounds

    # Filter agents if specified
    if agent_filter:
        original_agents = agents_module.agents.copy()
        agents_module.agents = {k: v for k, v in original_agents.items() if k in agent_filter}

    results = []
    errors = []

    def observer(round_num, total_rounds, agents_list, shops):
        if round_num == total_rounds - 1:
            results.append((agents_list, total_rounds))
        return True

    try:
        sim.run_sim(observer={'on_round_end': observer}, quiet=True)
    except Exception as e:
        errors.append(('sim', str(e), traceback.format_exc()))
    finally:
        sim.num_rounds = original_rounds
        if agent_filter:
            agents_module.agents = original_agents

    if not results:
        return {'errors': errors} if errors else None

    agents_list, total_rounds = results[0]

    # Calculate metrics
    agent_data = []
    for a in agents_list:
        profit = a['coin'] - STARTING_COIN
        ppr = profit / total_rounds
        tpr = a['time'] / total_rounds * 1000
        eff = calc_efficiency(ppr, tpr)
        agent_data.append({
            'name': a['name'],
            'coin': a['coin'],
            'ppr': ppr,
            'tpr': tpr,
            'eff': eff
        })

    # Sort by efficiency to determine winner
    agent_data.sort(key=lambda x: x['eff'], reverse=True)
    winner = agent_data[0]['name'] if agent_data else None

    return {'agents': agent_data, 'winner': winner, 'errors': errors}


def get_agent_files_mtime():
    """Get the most recent modification time of agent files."""
    agent_files = glob.glob('agents/*.py')
    if not agent_files:
        return 0
    return max(os.path.getmtime(f) for f in agent_files)


def run_benchmark(args, agent_filter):
    """Run a single benchmark cycle."""
    print(f"\nRunning {args.num_sims} sims, {args.rounds} rounds", end='')
    if args.jobs > 1:
        print(f", {args.jobs} workers", end='')
    if agent_filter:
        print(f", agents: {', '.join(agent_filter)}", end='')
    print()
    print("=" * 70)

    start = time.time()

    # Prepare simulation arguments
    sim_args = [(i, args.rounds, agent_filter) for i in range(args.num_sims)]

    wins = defaultdict(int)
    total_eff = defaultdict(float)
    total_ppr = defaultdict(float)
    total_tpr = defaultdict(float)
    total_coin = defaultdict(float)
    completed = 0

    if args.jobs > 1:
        with ProcessPoolExecutor(max_workers=args.jobs) as executor:
            futures = [executor.submit(run_single_sim, arg) for arg in sim_args]
            for future in as_completed(futures):
                result = future.result()
                if result:
                    wins[result['winner']] += 1
                    for a in result['agents']:
                        total_eff[a['name']] += a['eff']
                        total_ppr[a['name']] += a['ppr']
                        total_tpr[a['name']] += a['tpr']
                        total_coin[a['name']] += a['coin']
                completed += 1
                pct = completed * 100 // args.num_sims
                bar = '#' * (pct // 5) + '.' * (20 - pct // 5)
                elapsed = time.time() - start
                print(f"\r[{bar}] {completed}/{args.num_sims} ({elapsed:.1f}s)", end='', flush=True)
    else:
        for sim_arg in sim_args:
            result = run_single_sim(sim_arg)
            if result:
                wins[result['winner']] += 1
                for a in result['agents']:
                    total_eff[a['name']] += a['eff']
                    total_ppr[a['name']] += a['ppr']
                    total_tpr[a['name']] += a['tpr']
                    total_coin[a['name']] += a['coin']
            completed += 1
            pct = completed * 100 // args.num_sims
            bar = '#' * (pct // 5) + '.' * (20 - pct // 5)
            elapsed = time.time() - start
            print(f"\r[{bar}] {completed}/{args.num_sims} ({elapsed:.1f}s)", end='', flush=True)

    elapsed = time.time() - start
    print(f"\r[{'#' * 20}] Done in {elapsed:.1f}s" + " " * 20)
    print()

    # Results
    print(f"{'AGENT':28} {'WINS':>6} {'WIN%':>7} {'AVG EFF':>12} {'AVG $/r':>10} {'AVG ms/r':>12}")
    print("-" * 80)

    n = args.num_sims
    for name in sorted(total_eff.keys(), key=lambda x: total_eff[x], reverse=True):
        avg_eff = total_eff[name] / n
        avg_ppr = total_ppr[name] / n
        avg_tpr = total_tpr[name] / n
        win_pct = wins[name] * 100 / n
        print(f"{name:28} {wins[name]:>6} {win_pct:>6.1f}% {avg_eff:>12,.1f} {avg_ppr:>+10,.0f} {avg_tpr:>12.5f}")

    print()
    print(f"Throughput: {n / elapsed:.1f} sims/sec, {n * args.rounds / elapsed:.0f} rounds/sec")
    return elapsed


def main():
    parser = argparse.ArgumentParser(description='Benchmark trading agents')
    parser.add_argument('-n', '--num-sims', type=int, default=10, help='Number of simulations')
    parser.add_argument('-r', '--rounds', type=int, default=200, help='Rounds per simulation')
    parser.add_argument('-j', '--jobs', type=int, default=1, help='Parallel workers')
    parser.add_argument('--only', type=str, help='Comma-separated list of agents to test')
    parser.add_argument('-w', '--watch', action='store_true', help='Watch for file changes and rerun')
    parser.add_argument('-d', '--debug', action='store_true', help='Run single sim with full debug output')
    args = parser.parse_args()

    agent_filter = set(args.only.split(',')) if args.only else None

    # Debug mode - run single sim with verbose output
    if args.debug:
        import sim
        print("Running single simulation with debug output...")
        print("=" * 70)
        sim.run_sim(debug_log=True, quiet=False)
        print("\nDebug log written to: debug_log.txt")
        return

    if args.watch:
        print("Watch mode: Will rerun when agents/*.py files change. Ctrl+C to stop.")
        last_mtime = 0
        try:
            while True:
                current_mtime = get_agent_files_mtime()
                if current_mtime > last_mtime:
                    if last_mtime > 0:
                        print("\n" + "=" * 70)
                        print("File change detected! Reloading...")
                        # Reload agent modules
                        import agents
                        for name in list(sys.modules.keys()):
                            if name.startswith('agents'):
                                importlib.reload(sys.modules[name])
                    run_benchmark(args, agent_filter)
                    last_mtime = current_mtime
                    print("\nWatching for changes... (Ctrl+C to stop)")
                time.sleep(0.5)
        except KeyboardInterrupt:
            print("\nStopped.")
    else:
        run_benchmark(args, agent_filter)


if __name__ == '__main__':
    main()
