# Simple Agent Ideas Brainstorm

## Core Philosophy
Abandon complex lookahead. Focus on:
- Global price awareness (computed once per round)
- Simple movement heuristics
- Cash-adaptive thresholds

---

## Movement Strategies

### 1. Sell-Seeking Movement
Move toward nodes where we can sell current inventory at good prices.
```
for each neighbor:
    score = sum(my_inventory[res] * neighbor_buy_price[res] / global_max[res])
pick highest score (or random from top-N)
```

### 2. Buy-Seeking Movement
Move toward nodes with cheap inventory relative to global.
```
for each neighbor:
    score = sum(qty * (global_max[res] - sell_price[res]))
pick highest (bargain hunting)
```

### 3. Hybrid: Sell-then-Buy
- If holding inventory: seek sell locations
- If low inventory: seek buy locations

### 4. Gradient Descent on Global Prices
Move toward nodes that are "uphill" for selling, "downhill" for buying.

### 5. Anti-Revisit
Track last N visited nodes, avoid them to explore more.

### 6. Heat-Seeking
Precompute "heat" of each node (total trade volume), move toward hot nodes.

### 7. Random with Bias
Random choice but weighted by some simple score.

---

## Buying Strategies

### 1. Buy Everything Profitable
Current simple_random approach. No filtering.

### 2. Cash-Adaptive ROI Threshold
- Poor: buy anything with margin > 0
- Rich: require margin/price > X%

### 3. Global-Relative Threshold
Only buy if we can sell at Y% of global max.
- Poor: Y = 60%
- Rich: Y = 90%

### 4. Inventory-Limited
Cap total inventory value to Z% of cash (liquidity management).

### 5. Best-Only
Only buy the single highest-margin item per round.

### 6. Quantity-Limited
Buy max N units per resource to diversify.

---

## Selling Strategies

### 1. Sell Everything
Current approach. Simple and fast.

### 2. Global Threshold
Only sell at X% of global max.

### 3. Cash-Adaptive Threshold
- Poor: sell at 60%+ of global max (need cash)
- Rich: sell at 95%+ (can wait)

### 4. Hold-for-Better
If we're moving toward a better sell price, hold.

### 5. NAS Hybrid
Sell here if price >= destination price.

---

## Threshold Schedules

### 1. Linear by Cash
threshold = base + slope * (cash / max_cash)

### 2. Step Function
if cash < 1000: loose
elif cash < 5000: medium
else: tight

### 3. Round-Based
Early rounds: loose (build capital)
Late rounds: tight (maximize final)

### 4. Inventory-Based
More inventory = more eager to sell

---

## Combinations to Test

| # | Movement | Buying | Selling | Threshold |
|---|----------|--------|---------|-----------|
| A | Random | All profitable | All | None |
| B | Sell-seeking | All profitable | All | None |
| C | Buy-seeking | All profitable | All | None |
| D | Random | Global-relative | Global-threshold | Cash-adaptive |
| E | Sell-seeking | Global-relative | Global-threshold | Cash-adaptive |
| F | Hybrid sell/buy | ROI threshold | Cash-adaptive | Cash-adaptive |
| G | Random + anti-revisit | All profitable | All | None |
| H | Gradient descent | Global-relative | Global-threshold | Cash-adaptive |

---

## Quick Wins to Test First

1. **Sell-seeking movement** - move toward where we can sell inventory
2. **Buy-seeking movement** - move toward cheap goods
3. **Global threshold selling** - only sell at 80%+ of global max
4. **Anti-revisit** - don't go back to last 2-3 nodes
5. **Round-based loosening** - start loose, tighten by round 50

---

## Metrics to Track

- $/round (profit)
- ms/round (speed)
- Efficiency ($/ms)
- Pareto dominance (vs which agents?)
