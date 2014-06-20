import utils

def agent(world_state, *args, **kwargs):

    myPositon = world_state['you']['position']
    currentNode = world_state['world'][myPositon]
    currentNodeNeighbours = currentNode['neighbours']

    highestGold = world_state['world']

    lowestGoldValue = 99999;
    lowestGoldNode = 0;

    biggestGoldValue = 0;
    biggestGoldNode = 0;

    ITEM = 'GOLD'

    buys, sells = {}, {}

    #print currentNodeNeighbours

    

    #Iterate through all the nodes
    for node_key, node in world_state['world'].items():
        #Find the the node with the lowest gold sell price
        if node_key in currentNodeNeighbours or node_key is myPositon:
            if ITEM in node['resources']:
                if node['resources'][ITEM]['sell'] < lowestGoldValue:
                    if node['resources'][ITEM]['quantity'] > 0:
                        lowestGoldValue = node['resources'][ITEM]['sell']
                        lowestGoldNode = node_key
           
    #Iterate through all the nodes
    for node_key, node in world_state['world'].items():
        #Find the the node with the lowest gold sell price
        if node_key in currentNodeNeighbours or node_key is myPositon:
            if ITEM in node['resources']:
                if node['resources'][ITEM]['buy'] > biggestGoldValue:
                    biggestGoldValue = node['resources'][ITEM]['sell']
                    biggestGoldNode = node_key   


    #print "Lowest Node: " + str(lowestGoldNode) + " Value: " + str(lowestGoldValue) 
    #print "Biggest Node: " + str(biggestGoldNode) + " Value: " + str(biggestGoldValue) 

    #Check if I have more than 1 gold
    if world_state['you']['resources'].get(ITEM, 0) > 0:
        #Check if I am on lowestGold Node
        if world_state['you']['position'] == biggestGoldNode:
            
            #print "On Expensive node selling!"
            if biggestGoldValue > lowestGoldValue:
                sells[ITEM] = world_state['you']['resources'][ITEM]

            # I move to the sell point
            destination = lowestGoldNode
        else:
            destination = biggestGoldNode	
    elif world_state['you']['position'] == lowestGoldNode:

            #print "On cheap node buying!"
            
            _max = (world_state['you']['coin']/(currentNode['resources'][ITEM]['sell']))
            
            if lowestGoldValue < biggestGoldValue:
                if not utils.is_last_round(world_state):
                    buys[ITEM] = min(_max, currentNode['resources'][ITEM]['quantity'])

            # I move to the sell point
            destination = biggestGoldNode
    else:
        if not utils.is_last_round(world_state):
            if ITEM in world_state['you']['resources']:
                if currentNode['resources'][ITEM]['sell'] < biggestGoldValue:
                    if world_state['you']['resources'][ITEM] > 0:
                        _max = world_state['you']['coin']/(currentNode['resources'][ITEM]['sell'])
                        buys[ITEM] = min(_max, currentNode['resources'][ITEM]['quantity'])

        destination = lowestGoldNode


    #if  world_state["meta"]["current_round"] == world_state["meta"]["total_rounds"]-2:
    #    sells['GOLD'] = world_state['you']['resources']['GOLD']

    if utils.is_last_round(world_state):
        sells[ITEM] = world_state['you']['resources'][ITEM]

    return {
        'buy':     sells,
        'sell':    buys,
        'move': destination
    }
