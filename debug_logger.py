"""
Debug logger for Ekon simulation.
Writes detailed game state to a log file for debugging.
"""

import json
from datetime import datetime


class DebugLogger:
    def __init__(self, filename=None):
        if filename is None:
            filename = f"ekon_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        self.filename = filename
        self.file = open(filename, 'w')
        self._write(f"=== Ekon Debug Log Started {datetime.now()} ===\n")

    def _write(self, msg):
        self.file.write(msg + "\n")
        self.file.flush()

    def log_setup(self, world_graph, world_shops, world_agents):
        """Log initial game setup."""
        self._write("\n=== GAME SETUP ===")
        self._write(f"Nodes: {len(world_graph)}")
        self._write(f"Agents: {len(world_agents)}")

        self._write("\n--- Initial Agent States ---")
        for agent in world_agents:
            self._write(f"  {agent['name']}:")
            self._write(f"    coin: {agent['coin']}")
            self._write(f"    position: {agent['position']}")
            self._write(f"    resources: {agent['resources']}")

        self._write("\n--- Sample Shop States (first 5) ---")
        for i, (node, shop) in enumerate(list(world_shops.items())[:5]):
            self._write(f"  Node {node}: {shop}")

    def log_round_start(self, round_num, total_rounds, agents):
        """Log start of round with agent standings."""
        self._write(f"\n{'='*60}")
        self._write(f"ROUND {round_num + 1}/{total_rounds}")
        self._write(f"{'='*60}")

        sorted_agents = sorted(agents, key=lambda a: a['coin'], reverse=True)
        self._write("Standings:")
        for i, agent in enumerate(sorted_agents):
            self._write(f"  {i+1}. {agent['name']}: ${agent['coin']:,} at node {agent['position']} | resources: {agent['resources']}")

    def log_agent_turn(self, agent, state_passed, move_returned):
        """Log an agent's turn details."""
        self._write(f"\n--- {agent['name']}'s Turn ---")
        self._write(f"  Position: {agent['position']}")
        self._write(f"  Coin: {agent['coin']}")
        self._write(f"  Resources: {agent['resources']}")

        current_shop = state_passed['world'][agent['position']]['resources']
        self._write(f"  Current shop resources: {current_shop}")

        if move_returned:
            self._write(f"  Move returned: {move_returned}")
        else:
            self._write(f"  Move returned: None/Invalid")

    def log_transaction(self, agent_name, tx_type, resource, quantity, price, success, reason=None):
        """Log a buy/sell transaction."""
        status = "OK" if success else f"FAILED ({reason})"
        self._write(f"  [{tx_type.upper()}] {agent_name}: {quantity} {resource} @ ${price} = ${quantity * price} - {status}")

    def log_movement(self, agent_name, from_pos, to_pos, success, reason=None):
        """Log agent movement."""
        if success:
            self._write(f"  [MOVE] {agent_name}: {from_pos} -> {to_pos}")
        else:
            self._write(f"  [MOVE] {agent_name}: {from_pos} -> {to_pos} FAILED ({reason})")

    def log_agent_exception(self, agent_name, exception):
        """Log when an agent throws an exception."""
        self._write(f"  [EXCEPTION] {agent_name}: {type(exception).__name__}: {exception}")

    def log_round_end(self, agents):
        """Log end of round summary."""
        total_wealth = sum(a['coin'] for a in agents)
        total_resources = sum(sum(a['resources'].values()) for a in agents)
        self._write(f"\nRound Summary: Total wealth=${total_wealth:,}, Total resources={total_resources}")

    def log_final_results(self, agents):
        """Log final game results."""
        self._write(f"\n{'='*60}")
        self._write("FINAL RESULTS")
        self._write(f"{'='*60}")

        sorted_agents = sorted(agents, key=lambda a: a['coin'], reverse=True)
        for i, agent in enumerate(sorted_agents):
            self._write(f"  {i+1}. {agent['name']}")
            self._write(f"     Coin: ${agent['coin']:,}")
            self._write(f"     Resources: {agent['resources']}")
            self._write(f"     Time spent: {agent['time']:.4f}s")

    def close(self):
        self._write(f"\n=== Log Ended {datetime.now()} ===")
        self.file.close()
