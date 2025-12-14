# Agent Experiments & Learnings

This document tracks hypotheses tested, results, and learnings to avoid repeating failed experiments.

---

## Current Best: champion_v3

| Metric | Value |
|--------|-------|
| $/round | +$6,857 |
| ms/round | 0.17ms |
| Efficiency | 40,335 $/r/ms |

**Config:** depth-2 lookahead, ALL neighbors, no quantity cap, sell_threshold=0.75

---

## Iteration 1: Depth & Neighbor Pruning

**Question:** What's the optimal lookahead depth and neighbor count?

| Config | $/round | ms/round | Notes |
|--------|---------|----------|-------|
| depth1 | $3,126 | 0.009ms | Baseline |
| depth2 top2 | $4,277 | 0.030ms | |
| depth2 top4 | $5,049 | 0.054ms | **v1 champion** |
| depth2 ALL | $5,544 | 0.096ms | Best depth2 |
| depth3 top2 | $4,517 | 0.065ms | Worse than depth2! |
| depth3 top4 | $5,178 | 0.213ms | Slower AND less profit |

**Learnings:**
- More neighbors > more depth (counterintuitive!)
- depth2 with ALL neighbors beats depth3 with pruning
- Pruning to top-N has diminishing returns and sorting overhead

---

## Iteration 2: Parameter Tuning

Built on depth2 top4 baseline ($5,049/r @ 0.054ms)

### Future Discount (0.7 - 1.0)
| Value | Δ$/round | Verdict |
|-------|----------|---------|
| 0.7 | -31 | No impact |
| 0.8 | -14 | No impact |
| 0.9 | baseline | - |
| 0.95 | +10 | No impact |
| 1.0 | -3 | No impact |

**Learning:** Discount factor doesn't matter much. Keep at 0.9.

### Budget Reserve (keep % of coins back)
| Reserve | Δ$/round | Verdict |
|---------|----------|---------|
| 0% | baseline | - |
| 10% | -23 | HURTS |
| 20% | -23 | HURTS |

**Learning:** Use all available capital. Reserves waste money.

### Quantity Cap in Scoring
| Cap | Δ$/round | Verdict |
|-----|----------|---------|
| 50 | -39 | Worse |
| 100 | baseline | - |
| 200 | +114 | Better |
| none | **+443** | **BEST** |

**Learning:** Don't cap quantity - score full potential.

### Buy Strategy
| Strategy | Δ$/round | Verdict |
|----------|----------|---------|
| Buy all profitable | baseline | - |
| Buy single best only | -1,015 | **HURTS BADLY** |

**Learning:** Always buy multiple profitable items, not just the best one.

### Hub Bonus (extra score for high-connectivity nodes)
| Bonus | Δ$/round | Verdict |
|-------|----------|---------|
| 0 | baseline | - |
| 10 | -108 | HURTS |
| 50 | -1,248 | HURTS BADLY |
| 100 | -3,599 | DISASTER |

**Learning:** Hub heuristic is WRONG for this game. Ignore node connectivity.

### Minimum Margin Filter
| Min | Δ$/round | Verdict |
|-----|----------|---------|
| 0 | baseline | - |
| 1 | -40 | Slightly worse |
| 3 | -689 | HURTS |
| 5 | -2,779 | HURTS BADLY |

**Learning:** Don't filter low-margin trades. Small profits add up.

### Neighbor Count (with no qty cap)
| Top-N | $/round | ms/round | Notes |
|-------|---------|----------|-------|
| 4 | $5,511 | 0.072ms | |
| 5 | $5,760 | 0.067ms | |
| 6 | $5,849 | 0.080ms | |
| 7 | $5,936 | 0.092ms | |
| 8 | $6,008 | 0.104ms | |
| ALL | **$6,241** | 0.094ms | **BEST - faster than top8!** |

**Learning:** Sorting overhead exceeds pruning benefit when N>6. Just check all.

---

## Iteration 3: Multi-hop Carrying

Built on champion_v2 ($6,241/r @ 0.094ms)

**Hypothesis:** Global price awareness failed because we sold everything every round.
If we HOLD items until we reach a good price, we can capture more value.

### Sell Threshold (only sell at X% of global max)
| Threshold | Δ$/round | Verdict |
|-----------|----------|---------|
| 0% (sell all) | baseline | - |
| 50% | +100 | Slight help |
| 60% | +200 | Better |
| 70% | +435 | Good |
| **73-76%** | **+576** | **BEST (plateau)** |
| 80% | +269 | Starts declining |
| 90% | -301 | Too greedy |

**Learning:** Hold items until you can sell at 75% of global max. Sweet spot is 0.73-0.76.

### Global Buying (buy for global max, not neighbor)
| Config | Δ$/round | Verdict |
|--------|----------|---------|
| global_buy only | -6,319 | DISASTER |
| global + sell70 | -1,938 | Still bad |
| global + sell80 | -3,098 | Worse |

**Learning:** Global buying STILL doesn't work, even with sell threshold. The problem is buying items you can't sell at the next stop.

### Move Toward Best Sale
| Config | Δ$/round | Verdict |
|--------|----------|---------|
| sale_weight=0.3 | -767 | HURTS |
| sale_weight=0.5 | -3,326 | HURTS BADLY |

**Learning:** Don't bias movement toward sales. Arbitrage opportunities are more valuable.

---

## Failed Hypotheses (Don't Retry)

### Global Price Awareness
**Hypothesis:** Compute global max buy prices; buy items with high global potential.
**Result:** -$3,000/round (DISASTER)
**Why:** Buys items that can't be sold at immediate destination. Would need multi-hop carrying logic to work, but agent only does 1-hop arbitrage.

### Deeper Lookahead (depth 3+)
**Hypothesis:** Looking further ahead finds better paths.
**Result:** Slower AND less profitable than depth 2 with more neighbors.
**Why:** Exponential path explosion. Pruning to make it fast loses the good paths.

### Smart Positioning (Hub Bonus)
**Hypothesis:** Nodes with more neighbors have more future opportunities.
**Result:** -$108 to -$3,599/round
**Why:** In this game, arbitrage opportunity matters more than connectivity.

### Selective Trading (Margin Filters)
**Hypothesis:** Only take high-margin trades, skip low-margin noise.
**Result:** -$689 to -$2,779/round
**Why:** Many small trades > few large trades. Volume matters.

### Capital Reserves
**Hypothesis:** Keep some cash for emergencies.
**Result:** -$23/round
**Why:** Unused capital = missed opportunities. Always deploy fully.

---

## Ideas Not Yet Tested

- [x] ~~Multi-hop carrying~~ → Partially works! Sell threshold helps, but global buying still broken
- [ ] Resource memory (track purchase price, ensure profit on sale)
- [ ] Opponent modeling (avoid nodes where others are heading)
- [ ] Price prediction (resources get depleted, prices might change)
- [ ] Path caching (precompute common routes)
- [ ] Smarter inventory management (don't hold too long, opportunity cost)

---

## Version History

| Version | $/round | ms/round | Key Changes |
|---------|---------|----------|-------------|
| blitz | $1,500 | 0.008ms | 1-step, fastest |
| depth3 | $2,000 | 0.06ms | 3-step, top2 |
| lookahead | $3,000 | 2ms | 4-step simulation |
| champion_v1 | $5,052 | 0.057ms | depth2 top4 |
| champion_v2 | $6,241 | 0.094ms | depth2 ALL, no cap |
| champion_v3 | $6,857 | 0.17ms | + sell threshold 0.75 |
