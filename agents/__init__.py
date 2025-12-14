from . import matt_shitty_agent
from . import east_india_trade_company
from . import the_pirate_of_cakey
from . import chris_d_rockeffeler
from . import lookahead
from . import fast_lookahead
from . import fast_lookahead2
from . import global_arb
from . import ultrafast

agents = {
  "matt_shitty_agent": matt_shitty_agent.agent,
  "stewart_awesome_agent": east_india_trade_company.agent,
  "the_pirate_of_cakey": the_pirate_of_cakey.agent,
  "the_pirate_of_cakey_recurse": the_pirate_of_cakey.agent_slow,
  "chris_d_rockeffeler": chris_d_rockeffeler.agent,
  "lookahead": lookahead.agent,
  "fast_lookahead": fast_lookahead.agent,
  "fast_lookahead2": fast_lookahead2.agent,
  "global_arb": global_arb.agent,
  "ultrafast": ultrafast.agent,
}
