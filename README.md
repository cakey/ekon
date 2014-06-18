Ekon
====

### Process

Every turn God iterates over the list of agents, calling them with the world state. The agent returns what resources they want to buy and sell at their **current node**, and what node they wish to move to.

### Example world state

    {
        'you': {
            'position': 2,
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
                        'buy': 100
                        'sell': 100
                    }
                }
            }
            2: {
                'neighbours': {1:1, 3: 1}
                'resources': {
                    'silver': {
                        'quantity': 5000,
                        'buy': 100
                        'sell': 100
                    }
                }
            }
            3: {
                'neighbours': {"A": 1, 1
                'resources': {
                    'wood': {
                        'quantity': 5000,
                        'buy': 100
                        'sell': 100
                    }
                }
            }
        }

    }

### Example message

    {
        'buys':   [('gold', 1000), ('silver', 500)],
        'sells':  [('bronze', 100), ('wood', 200)],
        'move':   2,
    }