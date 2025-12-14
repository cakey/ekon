from . import matt_shitty_agent
from . import east_india_trade_company
from . import the_pirate_of_cakey
from . import chris_d_rockeffeler
from . import blitz
from . import lookahead
from . import champion_v1
from . import champion_v2
from . import champion_v3
from . import champion_v4
from . import champion_v5
from . import champion_v5_blitz
from . import zen
from . import experimental_v6
from . import experimental_v8

# See EXPERIMENTS.md for full hypothesis testing results

agents = {
  # Originals (baseline comparisons - all dominated by blitz)
  "matt_shitty_agent": matt_shitty_agent.agent,
  "stewart_awesome_agent": east_india_trade_company.agent,
  "the_pirate_of_cakey": the_pirate_of_cakey.agent,
  "chris_d_rockeffeler": chris_d_rockeffeler.agent,

  # Reference implementations
  "blitz": blitz.agent,           # $3,570/r @ 0.008ms (dominated by blitz+nas)
  "lookahead": lookahead.agent,   # $3,000/r @ 2ms (original best)

  # Champions (experiment winners)
  "champion_v1": champion_v1.agent,       # $5,023/r @ 0.052ms (depth2 top4)
  "champion_v2": champion_v2.agent,       # $6,298/r @ 0.086ms (dominated by v5)
  "champion_v3": champion_v3.agent,       # $6,823/r @ 0.168ms (max profit)
  "champion_v4": champion_v4.agent,       # $6,284/r @ 0.118ms (REGRESSION)
  "champion_v5": champion_v5.agent,       # $6,668/r @ 0.087ms (BEST - v2+NAS)
  "champion_v5_blitz": champion_v5_blitz.agent,  # $3,748/r @ 0.007ms (fastest)
  "zen": zen.agent,                       # $107/r @ 0.0017ms - dominates matt

  # Experimental v6 - zen variants (testing neighbor counts)
  "zen_3": experimental_v6.zen_3,
  "zen_4": experimental_v6.zen_4,
  "zen_5": experimental_v6.zen_5,
  "zen_6": experimental_v6.zen_6,
  "zen_8": experimental_v6.zen_8,
  "zen_all": experimental_v6.zen_all,

  # Experimental v8 - zen + NAS variants
  "zen_nas_2": experimental_v8.zen_nas_2,
  "zen_nas_3": experimental_v8.zen_nas_3,
  "zen_nas_4": experimental_v8.zen_nas_4,
  "zen_nas_5": experimental_v8.zen_nas_5,
  "zen_nas_6": experimental_v8.zen_nas_6,
  "zen_nas_8": experimental_v8.zen_nas_8,
  "zen_nas_all": experimental_v8.zen_nas_all,
}
