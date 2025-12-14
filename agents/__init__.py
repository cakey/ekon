# Pareto Frontier Agents
# Each agent represents a different profit/speed tradeoff
# See EXPERIMENTS.md for methodology and results

from . import zen
from . import zen_variants
from . import simple_random
from . import simple_global
from . import hybrid_greedy
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
    "zen_3": zen_variants.zen_3,            # $235/r @ 0.0020ms
    "simple_global": simple_global.agent,   # $2,011/r @ 0.0029ms (dominates simple_random, zen_8)
    "simple_random": simple_random.agent,   # $1,400/r @ 0.0040ms (dominated by simple_global)
    "zen_4": zen_variants.zen_4,            # $439/r @ 0.0024ms (dominated)
    "zen_5": zen_variants.zen_5,            # $785/r @ 0.0029ms (dominated)
    "zen_6": zen_variants.zen_6,            # $1,069/r @ 0.0032ms (dominated)
    "zen_8": zen_variants.zen_8,            # $1,623/r @ 0.0048ms (dominated by simple_global)

    # Fast tier (0.005-0.01ms)
    "zen_all": zen_variants.zen_all,        # $2,710/r @ 0.0074ms
    "hybrid_greedy": hybrid_greedy.agent,   # $2,761/r @ 0.0077ms (greedy movement + global selling)
    "blitz": blitz.agent,                   # $3,622/r @ 0.0082ms
    "blitz_nas": champion_v5_blitz.agent,   # $3,774/r @ 0.0084ms

    # Balanced tier (0.01-0.1ms)
    "depth2_top2_nas": depth2_top2_nas.agent,  # $4,972/r @ 0.0318ms (dominates depth2_top2)
    "adaptive": adaptive.agent,                # $4,995/r @ 0.0495ms
    "champion_v1": champion_v1.agent,       # $5,082/r @ 0.0472ms
    "champion_v6": champion_v6.agent,       # $6,775/r @ 0.073ms (dominates v5)

    # Max profit tier (0.1-0.2ms)
    "champion_v8": champion_v8.agent,       # $7,184/r @ 0.148ms (dominates v7)
    "champion_v7": champion_v7.agent,       # $6,996/r @ 0.148ms (dominated by v8)
    "champion_v3": champion_v3.agent,       # $6,515/r @ 0.161ms (dominated by v7)
}
