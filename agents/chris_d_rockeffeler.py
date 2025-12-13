import math
import utils as u

markup = 2

def profit(shop, current_position, you):

  resources = {resource: info for (resource, info) in shop['resources'].items() if resource in current_position['resources']}
  resource_profitability = sorted(resources.keys(), key = lambda x: resources[x]['buy'] - current_position['resources'][x]['sell'], reverse = True)

  gains = 0
  buy = {}
  coin_counter = you['coin']
  cost = 0

  for resource in resource_profitability:
    pos_markup = shop['resources'][resource]['buy'] / float(current_position['resources'][resource]['sell'])

    if pos_markup >= 1:
      quantity = 0
      if current_position['resources'][resource]['sell'] * current_position['resources'][resource]['quantity'] > coin_counter:
        quantity = math.floor(coin_counter / current_position['resources'][resource]['sell'])
      else:
        quantity = current_position['resources'][resource]['quantity']

      if quantity > 0: buy[resource] = quantity

      cost += current_position['resources'][resource]['sell'] * quantity
      coin_counter -= current_position['resources'][resource]['sell'] * quantity
      gains += shop['resources'][resource]['buy'] * quantity

  return (gains, buy)


def agent(world_state, *args, **kwargs):

  my_position   = world_state['you']['position']
  my_node       = world_state['world'][my_position]
  my_neighbours = my_node['neighbours']

  # Sell everything, if you can
  sell = world_state['you']['resources']

  buy_tuple = (my_position, 0, {})

  if not u.is_last_round(world_state):
    for shop_index in my_neighbours.keys():
      shop_profit = profit(world_state['world'][shop_index], my_node, world_state['you'])
      if shop_profit[0] > buy_tuple[1]: buy_tuple = (shop_index,) + shop_profit


  return {
    'resources_to_sell_to_shop':  sell,
    'resources_to_buy_from_shop': buy_tuple[2],
    'move': buy_tuple[0]
  }
