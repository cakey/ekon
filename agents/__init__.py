from . import matt_shitty_agent
from . import east_india_trade_company
from . import the_pirate_of_cakey
from . import chris_d_rockeffeler

agents = {
  "matt_shitty_agent": matt_shitty_agent.agent,
  "stewart_awesome_agent": east_india_trade_company.agent,
  "the_pirate_of_cakey": the_pirate_of_cakey.agent,
  "the_pirate_of_cakey_recurse": the_pirate_of_cakey.agent_slow,
  "chris_d_rockeffeler": chris_d_rockeffeler.agent
}
