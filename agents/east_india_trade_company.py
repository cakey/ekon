import random

def agent(world_state, *args, **kwargs):

    myPositon = world_state['you']['position']
    currentNode = world_state['world'][myPositon]
    currentNodeNeighbours = currentNode['neighbours']

    highestGold = world_state['world']

    lowestGoldValue = 99999;
    lowestGoldNode = 0;

    biggestGoldValue = 0;
    biggestGoldNode = 0;


    buys, sells = {}, {}

    #Iterate through all the nodes
    for node_key, node in world_state['world'].items():
    	#Find the the node with the lowest gold sell price
        if 'GOLD' in node['resources']:
            if node['resources']['GOLD']['sell'] < lowestGoldValue:
            	if node['resources']['GOLD']['quantity'] > 0:
           	        lowestGoldValue = node['resources']['GOLD']['sell']
           	        lowestGoldNode = node_key
           
    #Iterate through all the nodes
    for node_key, node in world_state['world'].items():
    	#Find the the node with the lowest gold sell price
        if 'GOLD' in node['resources']:
            if node['resources']['GOLD']['sell'] > biggestGoldValue:
           	    biggestGoldValue = node['resources']['GOLD']['sell']
           	    biggestGoldNode = node_key   


    #print lowestGoldValue
    #print "Lowest " + str(lowestGoldNode)
    #print biggestGoldValue
    #print "Biggest " + str(biggestGoldNode)

    #Check if I have more than 1 gold
    if  'GOLD' in world_state['you']['resources']:
        #Check if I am on lowestGold Node
        if world_state['you']['position'] == biggestGoldNode:
            
            #Sell all my gold
            sells['GOLD'] = world_state['you']['resources']['GOLD']
            # I move to the sell point
            destination = lowestGoldNode
        else:
            destination = biggestGoldNode	
    else:
        #Check if I am on lowestGold Node
        if world_state['you']['position'] == lowestGoldNode:
            
            #Sell all my gold
            max = (world_state['you']['coin']/(currentNode['resources']['GOLD']['sell']))

            if max > currentNode['resources']['GOLD']['quantity']:
                max = currentNode['resources']['GOLD']['quantity']

            buys['GOLD'] = max
            # I move to the sell point
            destination = biggestGoldNode
        else:
            destination = lowestGoldNode	


    #print destination

    return {
        'buy':     sells,
        'sell':    buys,
        'move': destination
    }
