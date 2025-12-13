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

    def __init__(self, tick_rate=1.0):
        self.tick_rate = tick_rate
        self.playing = False
        self.step_requested = False
        self.quit_requested = False
        self.current_state = None
        self.activity_log = deque(maxlen=20)
        self.lock = threading.Lock()
        self.state_updated = threading.Event()
        self.stdscr = None

    def log_activity(self, message):
        """Add a message to the activity log."""
        with self.lock:
            self.activity_log.append(message)

    def update_state(self, round_num, total_rounds, agents, world_shops):
        """Called by simulation to update display state."""
        with self.lock:
            self.current_state = {
                'round': round_num,
                'total_rounds': total_rounds,
                'agents': sorted(agents, key=lambda a: a['coin'], reverse=True),
                'shops': world_shops
            }
        self.state_updated.set()

    def should_continue(self):
        """Check if simulation should proceed to next round."""
        if self.quit_requested:
            return False

        if self.playing:
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

    def _draw_box(self, win, y, x, h, w, title=None):
        """Draw a box with optional title."""
        # Corners
        win.addch(y, x, curses.ACS_ULCORNER)
        win.addch(y, x + w - 1, curses.ACS_URCORNER)
        win.addch(y + h - 1, x, curses.ACS_LLCORNER)
        try:
            win.addch(y + h - 1, x + w - 1, curses.ACS_LRCORNER)
        except curses.error:
            pass  # Bottom right corner can fail

        # Horizontal lines
        for i in range(1, w - 1):
            win.addch(y, x + i, curses.ACS_HLINE)
            try:
                win.addch(y + h - 1, x + i, curses.ACS_HLINE)
            except curses.error:
                pass

        # Vertical lines
        for i in range(1, h - 1):
            win.addch(y + i, x, curses.ACS_VLINE)
            try:
                win.addch(y + i, x + w - 1, curses.ACS_VLINE)
            except curses.error:
                pass

        # Title
        if title:
            win.addstr(y, x + 2, f" {title} ")

    def _draw_screen(self):
        """Render the current state to the screen."""
        if self.stdscr is None:
            return

        self.stdscr.clear()
        max_y, max_x = self.stdscr.getmaxyx()

        with self.lock:
            state = self.current_state
            log_entries = list(self.activity_log)

        # Header
        status = "PLAYING" if self.playing else "PAUSED"
        if state:
            header = f"  EKON TRADING SIMULATION    Round: {state['round'] + 1}/{state['total_rounds']}   [{status}]  Speed: {self.tick_rate:.1f}s"
        else:
            header = f"  EKON TRADING SIMULATION    Initializing...   [{status}]"

        self._draw_box(self.stdscr, 0, 0, 3, max_x, "EKON")
        self.stdscr.addstr(1, 2, header[:max_x - 4])

        # Leaderboard section
        leaderboard_height = min(10, max_y - 12)
        self._draw_box(self.stdscr, 3, 0, leaderboard_height, max_x, "LEADERBOARD")

        if state and state['agents']:
            for i, agent in enumerate(state['agents'][:leaderboard_height - 2]):
                rank = i + 1
                name = agent['name'][:25]
                coin = agent['coin']
                pos = agent['position']
                resources = sum(agent['resources'].values()) if agent['resources'] else 0

                line = f" {rank}. {name:<26} ${coin:>10,}   Node {pos:<4}  [{resources} items]"
                try:
                    self.stdscr.addstr(4 + i, 2, line[:max_x - 4])
                except curses.error:
                    pass

        # Activity log section
        log_start = 3 + leaderboard_height
        log_height = max_y - log_start - 4
        if log_height > 2:
            self._draw_box(self.stdscr, log_start, 0, log_height, max_x, "RECENT ACTIVITY")

            visible_logs = log_entries[-(log_height - 2):]
            for i, entry in enumerate(visible_logs):
                try:
                    self.stdscr.addstr(log_start + 1 + i, 2, f"> {entry}"[:max_x - 4])
                except curses.error:
                    pass

        # Controls bar
        controls_y = max_y - 3
        self._draw_box(self.stdscr, controls_y, 0, 3, max_x, "CONTROLS")
        controls = "[SPACE] Play/Pause  [N] Step  [+/-] Speed  [Q] Quit"
        try:
            self.stdscr.addstr(controls_y + 1, 2, controls[:max_x - 4])
        except curses.error:
            pass

        self.stdscr.refresh()

    def _input_loop(self):
        """Handle keyboard input in separate thread."""
        self.stdscr.nodelay(True)
        while not self.quit_requested:
            try:
                key = self.stdscr.getch()
                if key == ord('q') or key == ord('Q'):
                    self.quit_requested = True
                elif key == ord(' '):
                    self.playing = not self.playing
                elif key == ord('n') or key == ord('N'):
                    self.step_requested = True
                elif key == ord('+') or key == ord('='):
                    self.tick_rate = max(0.1, self.tick_rate - 0.1)
                elif key == ord('-') or key == ord('_'):
                    self.tick_rate = min(5.0, self.tick_rate + 0.1)
            except curses.error:
                pass
            time.sleep(0.05)

    def _display_loop(self):
        """Update display in separate thread."""
        while not self.quit_requested:
            self._draw_screen()
            time.sleep(0.1)

    def run(self, sim_func):
        """
        Run the visualizer with a simulation function.

        Args:
            sim_func: A function that takes (observer_callback) and runs the simulation.
                     The callback receives (round_num, total_rounds, agents, shops).
        """
        def curses_main(stdscr):
            self.stdscr = stdscr
            curses.curs_set(0)  # Hide cursor

            # Start input handling thread
            input_thread = threading.Thread(target=self._input_loop, daemon=True)
            input_thread.start()

            # Start display update thread
            display_thread = threading.Thread(target=self._display_loop, daemon=True)
            display_thread.start()

            # Run simulation in main thread
            try:
                sim_func(self)
            except Exception as e:
                self.quit_requested = True
                raise

            # Wait a moment to show final state
            if not self.quit_requested:
                self.playing = False
                self._draw_screen()
                self.stdscr.nodelay(False)
                self.stdscr.addstr(self.stdscr.getmaxyx()[0] - 1, 2, "Simulation complete. Press any key to exit.")
                self.stdscr.refresh()
                self.stdscr.getch()

        curses.wrapper(curses_main)


def create_observer(visualizer):
    """
    Create an observer function for the simulation.

    Returns a dict with callbacks for the simulation to use.
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
