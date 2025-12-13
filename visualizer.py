"""
Terminal visualization for Ekon trading simulation.
Uses curses for interactive display with play/pause/step controls.
"""

import curses
import threading
import time
from collections import deque


class GameVisualizer:
    """Curses-based visualizer for the Ekon trading simulation."""

    def __init__(self, tick_rate=0.5):
        self.tick_rate = tick_rate
        self.max_speed = False
        self.playing = False
        self.step_requested = False
        self.quit_requested = False
        self.current_state = None
        self.activity_log = deque(maxlen=50)
        self.lock = threading.Lock()
        self.stdscr = None
        self.needs_redraw = True

    def log_activity(self, message):
        """Add a message to the activity log."""
        with self.lock:
            self.activity_log.append(message)
            self.needs_redraw = True

    def update_state(self, round_num, total_rounds, agents, world_shops):
        """Called by simulation to update display state."""
        with self.lock:
            self.current_state = {
                'round': round_num,
                'total_rounds': total_rounds,
                'agents': sorted(agents, key=lambda a: a['coin'], reverse=True),
                'shops': world_shops
            }
            self.needs_redraw = True

    def should_continue(self):
        """Check if simulation should proceed to next round."""
        if self.quit_requested:
            return False

        if self.playing:
            if not self.max_speed:
                time.sleep(self.tick_rate)
            return not self.quit_requested

        # Paused - wait for step or play
        while not self.quit_requested:
            if self.playing:
                return True
            if self.step_requested:
                self.step_requested = False
                return True
            time.sleep(0.05)

        return False

    def _safe_addstr(self, y, x, text, attr=0):
        """Safely add string, handling edge cases."""
        try:
            max_y, max_x = self.stdscr.getmaxyx()
            if y < 0 or y >= max_y or x < 0 or x >= max_x:
                return
            # Truncate text to fit
            available = max_x - x - 1
            if available <= 0:
                return
            self.stdscr.addstr(y, x, text[:available], attr)
        except curses.error:
            pass

    def _draw_hline(self, y, x, width):
        """Draw a horizontal line."""
        try:
            max_y, max_x = self.stdscr.getmaxyx()
            if y < 0 or y >= max_y:
                return
            self._safe_addstr(y, x, "-" * min(width, max_x - x - 1))
        except curses.error:
            pass

    def _draw_screen(self):
        """Render the current state to the screen."""
        if self.stdscr is None:
            return

        max_y, max_x = self.stdscr.getmaxyx()

        # Use erase instead of clear to reduce flicker
        self.stdscr.erase()

        with self.lock:
            state = self.current_state
            log_entries = list(self.activity_log)

        # Title bar
        status = "PLAYING" if self.playing else "PAUSED "
        if self.max_speed:
            speed_str = "MAX"
        else:
            speed_str = f"{self.tick_rate:.1f}s"
        if state:
            title = f" EKON  Round {state['round'] + 1}/{state['total_rounds']}  [{status}]  Speed: {speed_str} "
        else:
            title = f" EKON  Initializing...  [{status}] "

        self._safe_addstr(0, 0, "=" * max_x, curses.A_BOLD)
        self._safe_addstr(0, 2, title, curses.A_BOLD | curses.A_REVERSE)

        # Leaderboard
        self._safe_addstr(2, 0, " LEADERBOARD", curses.A_BOLD | curses.A_UNDERLINE)

        if state and state['agents']:
            # Calculate profit per round
            rounds_played = state['round'] + 1
            starting_coin = 10000  # From sim.py traveller_start_gold

            for i, agent in enumerate(state['agents'][:8]):
                y = 3 + i
                if y >= max_y - 8:
                    break
                rank = i + 1

                # Calculate dynamic name width based on terminal size
                fixed_width = 35  # rank + coin + ppr
                name_width = max(15, max_x - fixed_width - 4)
                name = agent['name'][:name_width].ljust(name_width)

                coin = f"${agent['coin']:>10,}"
                profit = agent['coin'] - starting_coin
                profit_per_round = profit / rounds_played
                ppr_str = f"{profit_per_round:>+8,.0f}/r"

                line = f" {rank}. {name} {coin}  {ppr_str}"
                # Pad to full width
                line = line.ljust(max_x - 1)

                # Highlight top 3
                attr = curses.A_BOLD if rank <= 3 else 0
                self._safe_addstr(y, 0, line, attr)

        # Separator
        log_start = min(12, max_y - 10)
        self._draw_hline(log_start, 0, max_x)

        # Activity log
        self._safe_addstr(log_start + 1, 0, " ACTIVITY LOG", curses.A_BOLD | curses.A_UNDERLINE)

        log_height = max_y - log_start - 5
        if log_height > 0:
            visible_logs = log_entries[-log_height:]
            for i, entry in enumerate(visible_logs):
                y = log_start + 2 + i
                if y >= max_y - 3:
                    break
                self._safe_addstr(y, 1, f"> {entry}")

        # Controls bar at bottom
        self._draw_hline(max_y - 2, 0, max_x)
        controls = " [SPACE] Play/Pause  [N] Step  [+/-] Speed  [M] Max Speed  [Q] Quit "
        self._safe_addstr(max_y - 1, 0, controls, curses.A_REVERSE)

        # Single refresh at the end
        self.stdscr.refresh()

    def run(self, sim_func):
        """
        Run the visualizer with a simulation function.

        Args:
            sim_func: A function that takes (visualizer) and runs the simulation.
        """
        def curses_main(stdscr):
            self.stdscr = stdscr

            # Proper curses setup
            curses.curs_set(0)          # Hide cursor
            stdscr.nodelay(True)        # Non-blocking input
            stdscr.timeout(50)          # 50ms timeout for getch

            # Start simulation in background thread
            sim_thread = threading.Thread(target=lambda: sim_func(self), daemon=True)
            sim_thread.start()

            # Main loop - handle input and redraw
            while not self.quit_requested:
                # Handle input
                try:
                    key = stdscr.getch()
                    if key == ord('q') or key == ord('Q'):
                        self.quit_requested = True
                    elif key == ord(' '):
                        self.playing = not self.playing
                        self.needs_redraw = True
                    elif key == ord('n') or key == ord('N'):
                        self.step_requested = True
                    elif key == ord('m') or key == ord('M'):
                        self.max_speed = not self.max_speed
                        self.needs_redraw = True
                    elif key == ord('+') or key == ord('='):
                        self.max_speed = False
                        self.tick_rate = max(0.1, self.tick_rate - 0.1)
                        self.needs_redraw = True
                    elif key == ord('-') or key == ord('_'):
                        self.max_speed = False
                        self.tick_rate = min(5.0, self.tick_rate + 0.1)
                        self.needs_redraw = True
                    elif key == curses.KEY_RESIZE:
                        self.needs_redraw = True
                except curses.error:
                    pass

                # Redraw screen
                self._draw_screen()

                # Check if simulation ended
                if not sim_thread.is_alive() and not self.quit_requested:
                    self.playing = False
                    self._draw_screen()
                    self._safe_addstr(self.stdscr.getmaxyx()[0] - 1, 0,
                                     " Simulation complete! Press Q to exit ".ljust(self.stdscr.getmaxyx()[1]),
                                     curses.A_REVERSE | curses.A_BOLD)
                    self.stdscr.refresh()
                    stdscr.nodelay(False)
                    while True:
                        key = stdscr.getch()
                        if key == ord('q') or key == ord('Q'):
                            break
                    break

        curses.wrapper(curses_main)


def create_observer(visualizer):
    """
    Create an observer function for the simulation.
    """
    def on_round_end(round_num, total_rounds, agents, world_shops):
        visualizer.update_state(round_num, total_rounds, agents, world_shops)
        return visualizer.should_continue()

    def on_agent_action(agent_name, action_type, details):
        visualizer.log_activity(f"{agent_name}: {action_type} {details}")

    return {
        'on_round_end': on_round_end,
        'on_agent_action': on_agent_action
    }
