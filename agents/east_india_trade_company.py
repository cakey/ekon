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
            if node['resources']['GOLD']['buy'] > biggestGoldValue:
           	    biggestGoldValue = node['resources']['GOLD']['sell']
           	    biggestGoldNode = node_key   


    #print "Lowest Node: " + str(lowestGoldNode) + " Value: " + str(lowestGoldValue) 
    #print "Biggest Node: " + str(biggestGoldNode) + " Value: " + str(biggestGoldValue) 

    #Check if I have more than 1 gold
    if world_state['you']['resources'].get('GOLD', 0) > 0:
        #Check if I am on lowestGold Node
        if world_state['you']['position'] == biggestGoldNode:
            
            #print "On Expensive node selling!"

            sells['GOLD'] = world_state['you']['resources']['GOLD']


            # I move to the sell point
            destination = lowestGoldNode
        else:
            destination = biggestGoldNode	
    elif world_state['you']['position'] == lowestGoldNode:

            #print "On cheap node buying!"
            
            _max = (world_state['you']['coin']/(currentNode['resources']['GOLD']['sell']))

            buys['GOLD'] = min(_max, currentNode['resources']['GOLD']['quantity'])

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
