# Pareto Frontier Agents
# Each agent represents a different profit/speed tradeoff
# See EXPERIMENTS.md for methodology and results

from . import zen
from . import zen_variants
from . import simple_random
from . import simple_global
from . import hybrid_greedy
from . import global_arb
from . import global_arb_fast
from . import global_arb_turbo
from . import global_arb_plus
from . import backtrack_fast
from . import depth2_global
from . import depth2_global_top4
from . import depth2_global_all
from . import hybrid_edge
from . import hybrid_champion
from . import max_profit
from . import ultimate
from . import blitz
from . import champion_v1
from . import champion_v3
from . import champion_v5_blitz
from . import champion_v6
from . import champion_v7
from . import champion_v8
from . import depth2_top2_nas
from . import adaptive

agents = {
    # Ultra-fast tier (0.001-0.005ms)
    "zen": zen.agent,                       # $117/r @ 0.0016ms
    "zen_3": zen_variants.zen_3,            # $235/r @ 0.0020ms (DOMINATED by global_arb_turbo)
    "global_arb_turbo": global_arb_turbo.agent,  # $1,678/r @ 0.0019ms (15x zen, DOMINATES zen_3!)
    "global_arb_fast": global_arb_fast.agent,  # $3,849/r @ 0.0026ms (fixed thresholds)
    "global_arb": global_arb.agent,         # $4,050/r @ 0.0030ms (DOMINATES simple_global, zen_all, blitz, blitz_nas)
    "global_arb_plus": global_arb_plus.agent,  # $4,218/r @ 0.0036ms (DOMINATED by backtrack_fast)
    "backtrack_fast": backtrack_fast.agent,   # $4,321/r @ 0.0034ms (DOMINATES global_arb_plus!)
    "simple_global": simple_global.agent,   # $2,011/r @ 0.0029ms (dominated by global_arb)
    "simple_random": simple_random.agent,   # $1,400/r @ 0.0040ms (dominated)
    "zen_4": zen_variants.zen_4,            # $439/r @ 0.0024ms (dominated)
    "zen_5": zen_variants.zen_5,            # $785/r @ 0.0029ms (dominated)
    "zen_6": zen_variants.zen_6,            # $1,069/r @ 0.0032ms (dominated)
    "zen_8": zen_variants.zen_8,            # $1,623/r @ 0.0048ms (dominated)

    # Fast tier (0.005-0.01ms) - ALL DOMINATED by global_arb
    "zen_all": zen_variants.zen_all,        # $2,710/r @ 0.0074ms (dominated by global_arb)
    "hybrid_greedy": hybrid_greedy.agent,   # $2,761/r @ 0.0077ms (dominated by global_arb)
    "blitz": blitz.agent,                   # $3,622/r @ 0.0082ms (dominated by global_arb)
    "blitz_nas": champion_v5_blitz.agent,   # $3,774/r @ 0.0084ms (dominated by global_arb)

    # Balanced tier (0.01-0.1ms) - hybrid_champion DOMINATES depth2 family
    "hybrid_edge": hybrid_edge.agent,           # $4,640/r @ 0.0100ms (fills gap: global_arb+ → depth2)
    "hybrid_champion": hybrid_champion.agent,   # $9,888/r @ 0.0191ms (DOMINATED by max_profit)
    "max_profit": max_profit.agent,             # $10,116/r @ 0.0172ms (DOMINATED by ultimate)
    "ultimate": ultimate.agent,                 # $11,065/r @ 0.0163ms (NEW MAX PROFIT! DOMINATES max_profit)
    "depth2_global": depth2_global.agent,       # $8,189/r @ 0.0263ms (dominated by hybrid_champion)
    "depth2_global_top4": depth2_global_top4.agent,  # $9,108/r @ 0.0379ms (dominated by hybrid_champion)
    "depth2_global_all": depth2_global_all.agent,    # $9,621/r @ 0.0895ms (dominated by hybrid_champion)
    "depth2_top2_nas": depth2_top2_nas.agent,  # $4,972/r @ 0.0318ms (dominated)
    "adaptive": adaptive.agent,                # $4,995/r @ 0.0495ms (dominated by depth2_global)
    "champion_v1": champion_v1.agent,       # $5,082/r @ 0.0472ms (dominated by depth2_global)
    "champion_v6": champion_v6.agent,       # $6,775/r @ 0.073ms (dominated by depth2_global)

    # Max profit tier (0.1-0.2ms) - DOMINATED by depth2_global
    "champion_v8": champion_v8.agent,       # $7,184/r @ 0.148ms (dominated by depth2_global)
    "champion_v7": champion_v7.agent,       # $6,996/r @ 0.148ms (dominated)
    "champion_v3": champion_v3.agent,       # $6,515/r @ 0.161ms (dominated)
}
