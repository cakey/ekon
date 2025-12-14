# Pareto Frontier Agents
# Each agent represents a different profit/speed tradeoff
# See EXPERIMENTS.md for methodology and results

from . import zen
from . import zen_variants
from . import blitz
from . import champion_v1
from . import champion_v3
from . import champion_v5
from . import champion_v5_blitz
from . import depth2_top2
from . import adaptive

agents = {
    # Ultra-fast tier (0.001-0.005ms)
    "zen": zen.agent,                       # $117/r @ 0.0017ms
    "zen_3": zen_variants.zen_3,            # $241/r @ 0.0020ms
    "zen_4": zen_variants.zen_4,            # $475/r @ 0.0025ms
    "zen_5": zen_variants.zen_5,            # $838/r @ 0.0029ms
    "zen_6": zen_variants.zen_6,            # $953/r @ 0.0033ms
    "zen_8": zen_variants.zen_8,            # $1,625/r @ 0.0044ms

    # Fast tier (0.005-0.01ms)
    "zen_all": zen_variants.zen_all,        # $2,710/r @ 0.0074ms
    "blitz": blitz.agent,                   # $3,622/r @ 0.0082ms
    "blitz_nas": champion_v5_blitz.agent,   # $3,774/r @ 0.0084ms

    # Balanced tier (0.01-0.1ms)
    "depth2_top2": depth2_top2.agent,       # $4,590/r @ 0.0278ms
    "adaptive": adaptive.agent,             # $4,987/r @ 0.0384ms
    "champion_v1": champion_v1.agent,       # $5,105/r @ 0.0516ms
    "champion_v5": champion_v5.agent,       # $6,668/r @ 0.0936ms (BEST efficiency)

    # Max profit tier (0.1ms+)
    "champion_v3": champion_v3.agent,       # $6,818/r @ 0.1765ms
}
