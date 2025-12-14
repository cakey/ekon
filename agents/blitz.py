"""
Blitz Agent - Maximum speed through minimal operations.

Every microsecond counts. Inline everything, minimize allocations.
"""

import random
_r = random.choice


def agent(ws, *a, **k):
    y = ws['you']
    p = y['position']
    c = y['coin']
    r = y['resources']
    w = ws['world']
    s = w[p]['resources']
    m = ws['meta']

    # Last round
    if m['current_round'] == m['total_rounds'] - 1:
        return {'resources_to_sell_to_shop': {x: q for x, q in r.items() if x in s and q > 0},
                'resources_to_buy_from_shop': {}, 'move': p}

    # Sell
    sl = {}
    for x, q in r.items():
        if q > 0 and x in s:
            sl[x] = q
            c += q * s[x]['buy']

    # Find best
    bn = p
    bp = 0
    bb = None

    for n in w[p]['neighbours']:
        ns = w[n]['resources']
        pr = 0
        bu = {}
        bc = c

        for x, i in s.items():
            q, pc = i['quantity'], i['sell']
            if q > 0 and pc > 0 and bc > 0:
                ni = ns.get(x)
                if ni and ni['buy'] > pc:
                    am = min(bc / pc, q)
                    bu[x] = am
                    bc -= am * pc
                    pr += (ni['buy'] - pc) * am

        if pr > bp:
            bp = pr
            bn = n
            bb = bu

    # Random exploration if no opportunity
    if not bb:
        nbs = list(w[p]['neighbours'].keys())
        bn = _r(nbs) if nbs else p

    return {'resources_to_sell_to_shop': sl, 'resources_to_buy_from_shop': bb or {}, 'move': bn}
