#!/usr/bin/env python3
"""
Run the Ekon trading simulation with terminal visualization.

Controls:
    SPACE - Play/Pause
    N     - Step one round
    +/-   - Speed up/slow down
    Q     - Quit

Debug log is written to ekon_debug_*.log
"""

import sys
import sim
from visualizer import GameVisualizer, create_observer


def main():
    debug = '--debug' in sys.argv or '-d' in sys.argv

    visualizer = GameVisualizer(tick_rate=0.5)

    def run_with_observer(vis):
        observer = create_observer(vis)
        sim.run_sim(observer=observer, debug_log=debug, quiet=True)

    visualizer.run(run_with_observer)

    if debug:
        print("Debug log written to ekon_debug_*.log")


if __name__ == '__main__':
    main()
