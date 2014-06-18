Ekon
====

### Example world state

    {
        0: {
            'neighbours': {1:1, 2:1, 3:1}
            'resources': {
                'gold': {
                    'quantity': 500.0,
                    'buy': 10.0
                    'sell': 10.0
                }
            }
        }
        1: {
            'neighbours': {2:1}
            'resources': {
                'bronze': {
                    'quantity': 500.0,
                    'buy': 10.0
                    'sell': 10.0
                }
            }
        }
        2: {
            'neighbours': {1:1, 3: 1}
            'resources': {
                'silver': {
                    'quantity': 500.0,
                    'buy': 10.0
                    'sell': 10.0
                }
            }
        }
        3: {
            'neighbours': {"A": 1, 1
            'resources': {
                'wood': {
                    'quantity': 500.0,
                    'buy': 10.0
                    'sell': 10.0
                }
            }
        }
    }

### Example message

    {
        'buys':   [('gold', 100.0), ('silver', 50.0)],
        'sells':  [('bronze', 10.0), ('wood', 20.0)],
        'move':   2,
    }