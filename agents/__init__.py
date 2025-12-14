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

# See EXPERIMENTS.md for full hypothesis testing results

agents = {
  # Originals (baseline comparisons)
  "matt_shitty_agent": matt_shitty_agent.agent,
  "stewart_awesome_agent": east_india_trade_company.agent,
  "the_pirate_of_cakey": the_pirate_of_cakey.agent,
  "chris_d_rockeffeler": chris_d_rockeffeler.agent,

  # Reference implementations
  "blitz": blitz.agent,           # $1,500/r @ 0.008ms (fastest)
  "lookahead": lookahead.agent,   # $3,000/r @ 2ms (original best)

  # Champions (experiment winners)
  "champion_v1": champion_v1.agent,  # $5,052/r @ 0.057ms (depth2 top4)
  "champion_v2": champion_v2.agent,  # $6,298/r @ 0.086ms (BEST EFFICIENCY: 73,398)
  "champion_v3": champion_v3.agent,  # $6,875/r @ 0.161ms (max profit, -42% eff vs v2)
  "champion_v4": champion_v4.agent,  # $6,284/r @ 0.118ms (REGRESSION - worse than v2)
}
