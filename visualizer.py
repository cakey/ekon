"""
Terminal visualization for Ekon trading simulation.
Uses curses for interactive display with play/pause/step controls.
"""

import curses
import threading
import time
from collections import deque, defaultdict

STARTING_COIN = 10000  # Must match sim.py


def calc_efficiency(ppr, tpr_ms):
    """Calculate efficiency: profit per round per ms of CPU time."""
    if tpr_ms <= 0.001:  # Avoid division by zero
        return ppr * 1000  # Treat as 0.001ms
    return ppr / tpr_ms


class SimStats:
    """Track aggregate statistics across multiple simulation runs."""

    def __init__(self):
        self.runs = 0
        self.wins = defaultdict(int)
        self.total_coins = defaultdict(int)
        self.total_profit_per_round = defaultdict(float)
        self.total_time_per_round = defaultdict(float)  # in ms
        self.total_efficiency = defaultdict(float)

    def record_run(self, agents, total_rounds):
        """Record results from a completed simulation."""
        self.runs += 1

        # Calculate efficiency for each agent and sort by it
        agents_with_eff = []
        for agent in agents:
            profit = agent['coin'] - STARTING_COIN
            ppr = profit / total_rounds if total_rounds > 0 else 0
            tpr_ms = (agent['time'] / total_rounds * 1000) if total_rounds > 0 else 0
            eff = calc_efficiency(ppr, tpr_ms)
            agents_with_eff.append((agent, eff, ppr, tpr_ms))

        # Winner is determined by efficiency ($/round/ms)
        sorted_agents = sorted(agents_with_eff, key=lambda x: x[1], reverse=True)

        # Record winner
        if sorted_agents:
            self.wins[sorted_agents[0][0]['name']] += 1

        # Record stats for each agent
        for agent, eff, ppr, tpr_ms in agents_with_eff:
            name = agent['name']
            self.total_coins[name] += agent['coin']
            self.total_profit_per_round[name] += ppr
            self.total_time_per_round[name] += tpr_ms
            self.total_efficiency[name] += eff

    def get_avg_coin(self, name):
        return self.total_coins[name] / self.runs if self.runs else 0

    def get_avg_ppr(self, name):
        return self.total_profit_per_round[name] / self.runs if self.runs else 0

    def get_avg_tpr(self, name):
        return self.total_time_per_round[name] / self.runs if self.runs else 0

    def get_avg_efficiency(self, name):
        return self.total_efficiency[name] / self.runs if self.runs else 0

    def get_win_rate(self, name):
        return self.wins[name] / self.runs if self.runs else 0


class GameVisualizer:
    """Curses-based visualizer for the Ekon trading simulation."""

    def __init__(self, tick_rate=0.5):
        self.tick_rate = tick_rate
        self.max_speed = False
        self.playing = False
        self.step_requested = False
        self.quit_requested = False
        self.restart_requested = False
        self.runs_to_do = 0  # Queue of simulations to run

        self.current_state = None
        self.activity_log = deque(maxlen=50)
        self.stats = SimStats()

        self.lock = threading.Lock()
        self.stdscr = None

    def reset_for_new_run(self):
        """Reset state for a new simulation run."""
        self.current_state = None
        self.activity_log.clear()
        self.restart_requested = False
        self.playing = False
        self.step_requested = False

    def log_activity(self, message):
        with self.lock:
            self.activity_log.append(message)

    def update_state(self, round_num, total_rounds, agents, world_shops):
        with self.lock:
            # Calculate metrics for each agent
            agents_with_metrics = []
            for agent in agents:
                a = dict(agent)
                rounds = round_num + 1
                a['time_per_round'] = (agent['time'] / rounds * 1000) if rounds > 0 else 0  # ms
                profit = agent['coin'] - STARTING_COIN
                a['profit_per_round'] = profit / rounds if rounds > 0 else 0
                a['efficiency'] = calc_efficiency(a['profit_per_round'], a['time_per_round'])
                agents_with_metrics.append(a)

            self.current_state = {
                'round': round_num,
                'total_rounds': total_rounds,
                'agents': sorted(agents_with_metrics, key=lambda a: a['efficiency'], reverse=True),
            }

    def record_results(self, agents, total_rounds):
        """Called when simulation ends to record stats."""
        with self.lock:
            self.stats.record_run(agents, total_rounds)

    def should_continue(self):
        """Check if simulation should proceed to next round."""
        if self.quit_requested or self.restart_requested:
            return False

        if self.playing:
            if not self.max_speed:
                time.sleep(self.tick_rate)
            return not (self.quit_requested or self.restart_requested)

        # Paused - wait for step, play, quit, or restart
        while True:
            if self.quit_requested or self.restart_requested:
                return False
            if self.playing:
                return True
            if self.step_requested:
                self.step_requested = False
                return True
            time.sleep(0.05)

    def _put(self, y, x, text, attr=0):
        """Safely add string to screen."""
        try:
            max_y, max_x = self.stdscr.getmaxyx()
            if 0 <= y < max_y and 0 <= x < max_x:
                self.stdscr.addstr(y, x, text[:max_x - x - 1], attr)
        except curses.error:
            pass

    def _hline(self, y, width):
        self._put(y, 0, "-" * width)

    def _draw(self):
        """Render current state."""
        if not self.stdscr:
            return

        max_y, max_x = self.stdscr.getmaxyx()
        self.stdscr.erase()

        with self.lock:
            state = self.current_state
            logs = list(self.activity_log)
            stats = self.stats

        # Title bar
        status = "PLAYING" if self.playing else "PAUSED"
        speed = "MAX" if self.max_speed else f"{self.tick_rate:.1f}s"
        if state:
            rnd = f"Round {state['round'] + 1}/{state['total_rounds']}"
        else:
            rnd = "Initializing..."
        runs_str = f"Runs: {stats.runs}" if stats.runs else ""
        if self.runs_to_do > 0:
            runs_str += f" (+{self.runs_to_do} queued)"

        title = f" EKON  {rnd}  [{status}]  Speed: {speed}  {runs_str} "
        self._put(0, 0, "=" * max_x, curses.A_BOLD)
        self._put(0, 2, title, curses.A_BOLD | curses.A_REVERSE)

        # Leaderboard (sorted by efficiency: $/round/ms)
        # Header row
        self._put(2, 0, " LEADERBOARD (by $/r/ms)", curses.A_BOLD | curses.A_UNDERLINE)
        # Column headers
        hdr = "     NAME                         EFF($/r/ms)         COIN      $/r        ms/r"
        if stats.runs > 0:
            hdr += "    WR"
        self._put(3, 0, hdr, curses.A_DIM)

        if state and state['agents']:
            for i, agent in enumerate(state['agents'][:7]):
                y = 4 + i
                if y >= max_y - 10:
                    break

                name = agent['name'][:28].ljust(28)
                coin = f"${agent['coin']:>12,}"
                ppr = agent.get('profit_per_round', 0)
                ppr_str = f"{ppr:>+8,.0f}"
                tpr = agent.get('time_per_round', 0)
                tpr_str = f"{tpr:>10.4f}"
                eff = agent.get('efficiency', 0)
                eff_str = f"{eff:>12,.1f}"

                # Show win rate if we have stats
                if stats.runs > 0:
                    wr = stats.get_win_rate(agent['name']) * 100
                    extra = f"  {wr:>4.0f}%"
                else:
                    extra = ""

                line = f" {i+1}. {name} {eff_str} {coin} {ppr_str} {tpr_str}{extra}"
                attr = curses.A_BOLD if i < 3 else 0
                self._put(y, 0, line, attr)

        # Aggregate stats section (if we have runs)
        stats_y = 13
        if stats.runs > 0 and stats_y < max_y - 8:
            self._hline(stats_y, max_x)
            self._put(stats_y + 1, 0, f" AGGREGATE ({stats.runs} runs)", curses.A_BOLD | curses.A_UNDERLINE)
            # Column headers for aggregate
            self._put(stats_y + 2, 0, "     NAME                         EFF($/r/ms)   WINS     WR%    AVG COIN      $/r        ms/r", curses.A_DIM)

            # Show agents sorted by average efficiency
            all_agents = list(stats.total_efficiency.keys())
            agents_by_eff = sorted(all_agents, key=lambda n: stats.get_avg_efficiency(n), reverse=True)

            for i, name in enumerate(agents_by_eff[:5]):
                y = stats_y + 3 + i
                if y >= max_y - 6:
                    break
                wr = stats.get_win_rate(name) * 100
                avg_coin = stats.get_avg_coin(name)
                avg_ppr = stats.get_avg_ppr(name)
                avg_tpr = stats.get_avg_tpr(name)
                avg_eff = stats.get_avg_efficiency(name)
                display_name = name[:28].ljust(28)
                line = f" {i+1}. {display_name} {avg_eff:>12,.1f}   {stats.wins[name]:>4}   {wr:>5.1f}% ${avg_coin:>12,.0f} {avg_ppr:>+8,.0f} {avg_tpr:>10.4f}"
                self._put(y, 0, line)
            log_start = stats_y + 3 + min(5, len(agents_by_eff)) + 1
        else:
            log_start = 12

        # Activity log
        if log_start < max_y - 5:
            self._hline(log_start, max_x)
            self._put(log_start + 1, 0, " ACTIVITY LOG", curses.A_BOLD | curses.A_UNDERLINE)

            log_height = max_y - log_start - 5
            for i, entry in enumerate(logs[-log_height:]):
                y = log_start + 2 + i
                if y >= max_y - 3:
                    break
                self._put(y, 1, f"> {entry}")

        # Controls
        self._hline(max_y - 2, max_x)
        self._put(max_y - 1, 0, " [SPACE] Play/Pause  [N] Step  [M] Max  [+/-] Speed  [R] Restart  [Q] Quit ", curses.A_REVERSE)

        self.stdscr.refresh()

    def _handle_key(self, key):
        """Process keyboard input."""
        if key == ord('q') or key == ord('Q'):
            self.quit_requested = True
        elif key == ord(' '):
            self.playing = not self.playing
        elif key == ord('n') or key == ord('N'):
            self.step_requested = True
        elif key == ord('m') or key == ord('M'):
            self.max_speed = not self.max_speed
        elif key == ord('r') or key == ord('R'):
            self.restart_requested = True
            self.playing = False
        elif key == ord('+') or key == ord('='):
            self.max_speed = False
            self.tick_rate = max(0.1, self.tick_rate - 0.1)
        elif key == ord('-') or key == ord('_'):
            self.max_speed = False
            self.tick_rate = min(5.0, self.tick_rate + 0.1)

    def _run_batch(self, sim_func, count):
        """Run multiple simulations in max speed mode."""
        old_max_speed = self.max_speed
        old_playing = self.playing
        self.max_speed = True
        self.playing = True

        for i in range(count):
            if self.quit_requested:
                break
            self.reset_for_new_run()
            self.runs_to_do = count - i - 1
            self.playing = True
            self.max_speed = True
            sim_func(self)

        self.runs_to_do = 0
        self.max_speed = old_max_speed
        self.playing = old_playing

    def run(self, sim_func):
        """Run the visualizer with simulation function."""

        def curses_main(stdscr):
            self.stdscr = stdscr
            curses.curs_set(0)
            stdscr.nodelay(True)
            stdscr.timeout(50)

            while not self.quit_requested:
                self.reset_for_new_run()

                # Run simulation in background
                sim_thread = threading.Thread(target=lambda: sim_func(self), daemon=True)
                sim_thread.start()

                # Main loop
                while not self.quit_requested and not self.restart_requested:
                    try:
                        key = stdscr.getch()
                        if key != -1:
                            self._handle_key(key)
                    except curses.error:
                        pass

                    self._draw()

                    # Sim ended naturally
                    if not sim_thread.is_alive() and not self.restart_requested:
                        self._show_end_screen(stdscr, sim_func)
                        break

        curses.wrapper(curses_main)

    def _show_end_screen(self, stdscr, sim_func):
        """Show end-of-simulation options."""
        self._draw()
        prompt = " [1] +1  [T] +10  [H] +100  [Q] Quit "
        self._put(self.stdscr.getmaxyx()[0] - 1, 0,
                  prompt.ljust(self.stdscr.getmaxyx()[1] - 1),
                  curses.A_REVERSE | curses.A_BOLD)
        self.stdscr.refresh()

        stdscr.nodelay(False)
        while not self.quit_requested:
            key = stdscr.getch()

            if key == ord('q') or key == ord('Q'):
                self.quit_requested = True
            elif key == ord('1'):
                self.restart_requested = True
                break
            elif key == ord('t') or key == ord('T'):
                # Run 10 in background with display updates
                stdscr.nodelay(True)
                stdscr.timeout(50)
                batch_thread = threading.Thread(
                    target=lambda: self._run_batch(sim_func, 10), daemon=True)
                batch_thread.start()
                while batch_thread.is_alive() and not self.quit_requested:
                    try:
                        key = stdscr.getch()
                        if key == ord('q') or key == ord('Q'):
                            self.quit_requested = True
                    except curses.error:
                        pass
                    self._draw()
                if not self.quit_requested:
                    self._show_end_screen(stdscr, sim_func)
                return
            elif key == ord('h') or key == ord('H'):
                stdscr.nodelay(True)
                stdscr.timeout(50)
                batch_thread = threading.Thread(
                    target=lambda: self._run_batch(sim_func, 100), daemon=True)
                batch_thread.start()
                while batch_thread.is_alive() and not self.quit_requested:
                    try:
                        key = stdscr.getch()
                        if key == ord('q') or key == ord('Q'):
                            self.quit_requested = True
                    except curses.error:
                        pass
                    self._draw()
                if not self.quit_requested:
                    self._show_end_screen(stdscr, sim_func)
                return

        stdscr.nodelay(True)
        stdscr.timeout(50)


def create_observer(visualizer):
    """Create observer callbacks for the simulation."""

    def on_round_end(round_num, total_rounds, agents, world_shops):
        visualizer.update_state(round_num, total_rounds, agents, world_shops)

        # Record final results on last round
        if round_num == total_rounds - 1:
            visualizer.record_results(agents, total_rounds)

        return visualizer.should_continue()

    def on_agent_action(agent_name, action_type, details):
        visualizer.log_activity(f"{agent_name}: {action_type} {details}")

    return {
        'on_round_end': on_round_end,
        'on_agent_action': on_agent_action,
    }
