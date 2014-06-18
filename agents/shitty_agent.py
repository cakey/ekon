def agent(world_state, *args, **kwargs):

    my_position = world_state['you']['position']
    my_node = world_state['world'][my_position]
    my_neighbours = my_node['neighbours']

    destination = random.sample(my_neighbours.items())


    buys, sells = {}, {}

    # Just fucking buy 100 of anything you can afford
    for resource, info in my_node['resources'].iteritems():
        if info['quantity'] >= 100 and info['buy'] * 100 <= world_state['you']['coins']:
            buys['resource'] = 100

    # Sell as many resources as you bought to try not to stockpile
    bought_resource_count = 100 * len(sells)

    for i in range(0, bought_resource_count):
        random_resource = random.sample(world_state['you']['resources'].items())
        # TODO

    return {
        'buys':     buys,
        'sells':    sells,
        'move': destination
    }
