Ekon
====

### Process

Every turn God iterates over the list of agents, calling them with the world state. The agent returns what resources they want to buy and sell at their **current node**, and what node they wish to move to.

### Example world state

    {
        'you': {
            'position': 2,
            'coin': 2000,
            'resources': {
                'bronze': 40,
                'gold' : 800,
            }
        },
        'world': {
            0: {
                'neighbours': {1:1, 2:1, 3:1}
                'resources': {
                    'gold': {
                        'quantity': 5000,
                        'buy': 100
                        'sell': 100
                    }
                }
            }
            1: {
                'neighbours': {2:1}
                'resources': {
                    'bronze': {
                        'quantity': 5000,
                        'buy': 100,
                        'sell': 100
                    }
                }
            }
            2: {
                'neighbours': {1:1, 3:1}
                'resources': {
                    'silver': {
                        'quantity': 5000,
                        'buy': 100,
                        'sell': 100
                    }
                }
            }
            3: {
                'neighbours': {2: 1}
                'resources': {
                    'wood': {
                        'quantity': 5000,
                        'buy': 100,
                        'sell': 100
                    }
                }
            }
        }

    }

### Example message

    {
        'buy':   {"gold": 1000, "silver": 200},
        'sell':  {"wood": 300, "silver": 200},
        'move':   2,
    }

### Winning

Winner is the agent with the most coin at the end of the rounds.


### TODO

* Pass location of other players?
* Regeneration of resources?
* pass through round number so can sell off at end
* clean up logging
* cleanup buy/sell confusion

Done:
* allow only % of edges
* allow to move to same location
* buy price should be < sell price
* shuffle order turn of players per round
* not all shops have all resources
