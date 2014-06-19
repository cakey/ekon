import random

def agent(world_state, *args, **kwargs):

    myPositon = world_state['you']['position']
    currentNode = world_state['world'][myPositon]
    currentNodeNeighbours = currentNode['neighbours']


    destination = currentNodeNeighbours.keys()[0]

    print destination
    buys, sells = {}, {}

    # Buy as much gold as possible on current node
    if 'GOLD' in currentNode['resources']:
        buys['GOLD'] = 30

    sells['GOLD'] = 1


    return {
        'buy':     sells,
        'sell':    buys,
        'move': destination
    }
