#!/usr/bin/env python3
"""
Run the Ekon trading simulation with terminal visualization.

Controls:
    SPACE - Play/Pause
    N     - Step one round
    +/-   - Speed up/slow down
    Q     - Quit
"""

import sim
from visualizer import GameVisualizer, create_observer


def main():
    visualizer = GameVisualizer(tick_rate=0.5)

    def run_with_observer(vis):
        observer = create_observer(vis)
        sim.run_sim(observer=observer)

    visualizer.run(run_with_observer)


if __name__ == '__main__':
    main()
