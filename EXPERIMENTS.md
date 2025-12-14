# Agent Experiments & Learnings

This document tracks hypotheses tested, results, and learnings to avoid repeating failed experiments.

---

## Experiment Cycle

**Start by brainstorming ideas, then pick one and test it.**

### Brainstorming Prompts

When looking for new optimizations, ask:
- What information is available but unused?
- What could we cache/precompute? (prices static, quantities not; agents have persistent state now)
- Where are gaps in the frontier? (big jump = opportunity)
- What do profitable agents do that fast ones skip?
- What assumptions might be wrong?
- See "Ideas Not Yet Tested" section for backlog

### Testing

- Test ideas against frontier agents: `python3 experiment.py --all -n 30`
- **MANDATORY CHECK:** Is the new agent dominated by ANY existing agent?
  - If dominated → FAILED, don't add to registry, document why
  - If on frontier → SUCCESS, add to registry and frontier table
- We don't care about profit alone or speed alone. Only the frontier matters.

---

## Current Frontier

| Agent | $/round | ms/round | Efficiency | Position |
|-------|---------|----------|------------|----------|
| zen | $117 | 0.0016ms | 72,273 | ultra-fast |
| zen_3 | $235 | 0.0020ms | 118,708 | |
| **global_arb** | **$4,050** | **0.0030ms** | **1,343,195** | **DOMINATES simple_global, zen_all, blitz, blitz_nas** |
| simple_global | $2,011 | 0.0029ms | 689,137 | dominated by global_arb |
| zen_all | $2,710 | 0.0074ms | 363,860 | dominated by global_arb |
| hybrid_greedy | $2,761 | 0.0077ms | 358,634 | dominated by global_arb |
| blitz | $3,622 | 0.0082ms | 439,690 | dominated by global_arb |
| champion_v5_blitz | $3,774 | 0.0084ms | 449,332 | dominated by global_arb |
| depth2_top2_nas | $4,972 | 0.0318ms | 156,352 | dominates depth2_top2 |
| adaptive | $4,995 | 0.0495ms | 100,909 | |
| champion_v1 | $5,082 | 0.0472ms | 107,567 | balanced-fast |
| champion_v6 | $6,775 | 0.073ms | 93,349 | balanced (dominates v5) |
| champion_v7 | $6,996 | 0.148ms | 47,320 | dominated by v8 |
| **champion_v8** | **$7,184** | **0.148ms** | **48,541** | **max profit (dominates v7)** |

*Updated after Iteration 29 (global_arb agent)*

**Validation Rules:**
1. New agent beats at least one frontier agent on at least one metric
2. New agent is NOT strictly dominated (worse on ALL metrics) by any frontier agent
3. If dominated → discard. If on frontier → keep as new option.

---

## Why Test Against ALL Frontier Agents?

Testing an idea against only one baseline can mislead:
- Idea X might help v2 but hurt blitz
- Without testing both, we'd wrongly conclude "X is good" or "X is bad"
- Testing all reveals: "X helps slower agents but hurts fast ones" → real insight

**Example (sell_threshold=0.75):**
- On v2: Added $577/r but cost 0.075ms → created v3, worse efficiency
- Should have also tested: blitz+threshold, v1+threshold
- Might have revealed: threshold only helps when you have depth-2 lookahead

---

## Current Best: champion_v2 (by efficiency)

| Metric | v2 (efficient) | v3 (max profit) |
|--------|----------------|-----------------|
| $/round | +$6,298 | +$6,875 |
| ms/round | 0.086ms | 0.161ms |
| Efficiency | **73,398** | 42,774 |

**v2 Config:** depth-2 lookahead, ALL neighbors, no quantity cap
**v3 Config:** + sell_threshold=0.75 (adds $577/r but costs 0.075ms)

**Note:** v3 trades efficiency for profit. v4 attempted to recover efficiency but ended up worse than v2 on both metrics. See "V4 Summary" for details.

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

## Iteration 4: Efficiency Optimization

Built on champion_v3 ($6,857/r @ 0.17ms, eff=40,335)

**Goal:** Improve $/round/ms efficiency. Blitz is 12x more efficient - can we get champion profits at better speed?

### Approach 1: Blitz + Sell Threshold
**Hypothesis:** Combine fastest agent (blitz) with best finding (sell_threshold=0.75)
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| blitz | $3,585 | 0.007ms | 501,036 | baseline |
| blitz+threshold | $3,684 | 0.079ms | 46,440 | WORSE efficiency |

**Learning:** Sell threshold hurts blitz! It needs depth-2 lookahead to find good sell locations. Without it, holding items just means missing immediate sales.

### Approach 2: Depth 1 + Sell Threshold
**Hypothesis:** Maybe depth 2 isn't needed if we have global price awareness.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| depth1+threshold | $3,293 | 0.080ms | 41,326 | WORSE than blitz! |

**Learning:** Depth 1 is NOT enough. The sell threshold requires depth-2 to work - you need to see WHERE to go to sell high.

### Approach 3: Adaptive Depth
**Hypothesis:** Use depth 1 when profit is obvious (>5000), depth 2 only when unclear.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| adaptive (thresh=5000) | **$6,423** | **0.118ms** | **54,400** | **+32% efficiency!** |

**Learning:** BEST EFFICIENCY! Only 1.5% less profit than champion_v3, but 26% faster. The adaptive approach correctly skips depth-2 when not needed.

### Approach 4: Early Termination
**Hypothesis:** Stop searching once profit >= 8000 threshold.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| early_term (8000) | $1,293 | 0.090ms | 14,370 | **DISASTER** |

**Learning:** Threshold 8000 is WAY too aggressive. Terminates too early, picks bad paths. Need much lower threshold or don't use at all.

### Approach 5: No-Sort Single Pass
**Hypothesis:** Sorting is expensive. Track best without sorting.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| no_sort | $6,508 | 0.149ms | 43,726 | Marginal improvement |

**Learning:** Only +6.6% efficiency over champion_v3. Not worth the complexity.

### Approach 6: sqrt(qty) Scoring
**Hypothesis:** margin × qty overweights high-quantity items.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| sqrt_scoring | $6,413 | 0.153ms | 42,027 | No improvement |

**Learning:** Standard margin × qty scoring is correct. Don't change it.

### Approach 7: Margin-only Scoring
**Hypothesis:** Quantity doesn't matter for direction choice.
| Config | $/round | ms/round | Efficiency | Verdict |
|--------|---------|----------|------------|---------|
| margin_only | $5,591 | 0.146ms | 38,344 | HURTS profit |

**Learning:** Quantity matters! Ignoring it costs ~$1,000/round.

### Adaptive Threshold Tuning

Fine-grained testing of adaptive depth thresholds (50 runs each):

| Threshold | $/round | ms/round | Efficiency |
|-----------|---------|----------|------------|
| 1000 | $5,453 | 0.117ms | 46,557 |
| 1500 | $5,675 | 0.117ms | 48,366 |
| 2000 | $5,832 | 0.120ms | 48,638 |
| 2500 | $5,910 | 0.122ms | 48,516 |
| 3000 | $6,001 | 0.125ms | 48,119 |
| **4000** | **$6,192** | **0.127ms** | **48,703** |
| champion_v3 | $6,568 | 0.172ms | 38,149 |

**Learning:** Efficiency plateau 48,000-49,000 from threshold 1500-4000. Within plateau, 4000 gives best profit. +27% efficiency over champion_v3.

### V4 Summary

**MISTAKE: Used wrong baseline!**

v4 was declared "winner" over v3, but v3 itself was an efficiency regression:

| Version | $/round | ms/round | Efficiency |
|---------|---------|----------|------------|
| champion_v2 | $6,298 | 0.086ms | **73,398** |
| champion_v3 | $6,875 | 0.161ms | 42,774 |
| champion_v4 | $6,284 | 0.118ms | 53,063 |

**v4 is strictly worse than v2** - less profit AND slower.

The sell_threshold feature (v3) adds ~$577/round profit but costs 0.075ms extra. That's only 7,693 $/ms efficiency for the feature itself - far below v2's 73,398 overall efficiency.

**Learning:** Always compare to the BEST previous version, not just the most recent. The sell_threshold may not be worth the computational cost.

---

## Iteration 5: Neighbor-Aware Selling (Testing Across Frontier)

**Idea:** Only sell resources if destination shop doesn't pay more (simpler than global threshold)

Tested on ALL frontier agents per methodology:

| Agent | Base $/r | +NAS $/r | Δ$/r | Base ms | +NAS ms | Verdict |
|-------|----------|----------|------|---------|---------|---------|
| blitz | $3,536 | $3,748 | **+$212** | 0.007 | 0.007 | **FRONTIER** |
| v1 | $5,023 | $1,288 | **-$3,735** | 0.052 | 0.045 | DISASTER |
| v2 | $6,240 | $6,668 | **+$428** | 0.088 | 0.087 | **DOMINATES v2!** |
| v3 | $6,823 | $6,668 | -$155 | 0.168 | 0.087 | tradeoff |

**Analysis - Why did it help/hurt each agent?**

1. **blitz+nas HELPS (+$212)**: Blitz is depth-1 with no sell awareness. NAS lets it capture value on next move without any time cost.

2. **v1+nas DISASTER (-$3,735)**: v1 has qty cap (100) and top-4 neighbor pruning. Its limited vision means it can't properly evaluate what to do with carried items. The scoring doesn't account for inventory value.

3. **v2+nas HELPS (+$428)**: v2 has full depth-2 visibility with ALL neighbors. It can properly evaluate where to carry items. NAS adds profit with negligible time cost.

4. **v3+nas TRADEOFF**: v3's global threshold (0.75) is MORE selective than NAS (local comparison). NAS sells more often → less profit but much faster (no global scan). Not strictly better or worse.

**Frontier Update:**
- **v2+nas dominates v2** → v2 removed from frontier
- **blitz+nas joins frontier** → new fastest profitable option
- v3+nas dominated by v2+nas (same profit, slower)

**Key Learning:** Ideas interact differently with agent architecture:
- NAS helps agents with good visibility (blitz, v2)
- NAS hurts agents with limited visibility (v1's caps/pruning)
- NAS conflicts with agents that already have sell logic (v3)

---

## Iteration 6: Ultra-Fast Agent (Dominate matt_shitty_agent)

**Problem:** matt_shitty_agent was on the Pareto frontier because it was the fastest agent, even though it lost money (-$49/r @ 0.0017ms). It's on the frontier because no other agent was both faster AND more profitable.

**Solution:** Create an agent faster than matt while still making profit.

**zen agent approach:**
- Sell everything we're holding (instant profit from carried items)
- Check first 2 neighbors for arbitrage opportunities
- Buy profitable items, move to best neighbor
- No sorting, no global scans, minimal computation

| Agent | $/round | ms/round | Result |
|-------|---------|----------|--------|
| matt_shitty_agent | -$49 | 0.0017ms | baseline |
| zen (2 neighbors) | +$117 | 0.0017ms | **DOMINATES matt** |

**Learning:** Even minimal arbitrage (2 neighbors, no optimization) beats random buying. Zen proves you can be profitable at any speed - the question is how much profit.

---

## Iteration 7: Fill the Zen→Blitz Gap

**Observation:** Huge gap between zen ($117/r @ 0.0017ms) and blitz ($3,622/r @ 0.0082ms). This is 4.8x slower for 31x more profit. What's in between?

**Hypothesis:** zen checks 2 neighbors, blitz checks ALL neighbors. Testing 3-8 neighbors should fill the gap proportionally.

**Created:** `agents/experimental_v6.py` with zen variants (factory pattern)

| Variant | Neighbors | $/round | ms/round | Efficiency |
|---------|-----------|---------|----------|------------|
| zen | 2 | $117 | 0.0017ms | 70,260 |
| zen_3 | 3 | $241 | 0.0020ms | 118,097 |
| zen_4 | 4 | $475 | 0.0025ms | 192,555 |
| zen_5 | 5 | $838 | 0.0029ms | 284,655 |
| zen_6 | 6 | $953 | 0.0033ms | 284,558 |
| zen_8 | 8 | $1,625 | 0.0044ms | 365,620 |
| zen_all | all | $2,710 | 0.0074ms | 363,860 |
| blitz | all | $3,622 | 0.0082ms | 439,690 |

**Results:**
- ALL zen variants are on the Pareto frontier!
- Efficiency peaks around zen_5/zen_6 (~284k) then increases again at zen_8/zen_all (~365k)
- Diminishing returns: zen_5 to zen_6 adds only $115/r for 0.0004ms
- Best efficiency jump: zen_4 to zen_5 nearly doubles profit for 16% more time

**Why does blitz beat zen_all?**
- Both check ALL neighbors
- Blitz has additional optimizations: local variable caching, pre-computed shop data
- zen_all is "naive all neighbors" - room for optimization

**Key Learning:** The relationship between neighbor count and profit is non-linear:
- 2→3 neighbors: +$124/r (+106%)
- 3→4 neighbors: +$234/r (+97%)
- 4→5 neighbors: +$363/r (+76%)
- 5→6 neighbors: +$115/r (+14%) ← diminishing returns start
- 6→8 neighbors: +$672/r (+71%) ← but more neighbors still helps
- 8→all: +$1,085/r (+67%)

**Frontier Impact:** Expanded from 6 agents to 12 agents. The gap is now filled with smooth profit/speed tradeoff options.

---

## Iteration 8: NAS on Zen Variants (FAILED)

**Hypothesis:** NAS helped blitz (+$212). Zen variants have similar structure, should benefit too.

**Prediction:** Each zen variant gains $100-300/r with minimal time increase.

**Results:**
| Variant | zen | zen_nas | Δ | Verdict |
|---------|-----|---------|---|---------|
| 2 | $104 | $92 | -$12 | HURTS |
| 3 | $229 | $201 | -$28 | HURTS |
| 4 | $454 | $410 | -$44 | HURTS |
| 5 | $739 | $808 | +$69 | helps |
| 6 | $1273 | $1166 | -$107 | HURTS |
| 8 | $1807 | $1652 | -$155 | HURTS |
| all | $2524 | $2607 | +$83 | helps |

**Analysis:** Prediction was WRONG. NAS hurts most zen variants.

Why? Zen evaluates neighbors using original coin (before selling). NAS holds items → less coin to buy with, but neighbor choice was already made assuming full sell. The decision sequence is wrong for NAS.

Blitz works differently - it factors actual coin during neighbor evaluation.

**Lesson:** Same idea (NAS) can help one architecture (blitz) and hurt another (zen) depending on decision sequence. Must understand HOW an agent evaluates before applying optimizations.

---

## Iteration 9: Why Blitz Beats Zen_all (NO FRONTIER IMPROVEMENT)

**Question:** Both check all neighbors, but blitz makes 34% more profit. Why?

**Investigation:**
1. Float vs int division? NO difference in profit
2. Random exploration? Found the cause!

**Results:**
| Agent | $/round | ms/round | Frontier? |
|-------|---------|----------|-----------|
| zen_all | $2,365 | 0.0072ms | yes |
| zen_float+rand | $3,570 | 0.0088ms | **NO - dominated by blitz** |
| blitz | $3,630 | 0.0077ms | yes |

**DOMINATED:** zen_float+rand is slower AND less profitable than blitz. Useless.

**Insight gained:** Random exploration when no trade exists adds ~$1,200/r. But this doesn't help us - blitz already does it better.

**Lesson:** Understanding WHY something works ≠ improving the frontier. Must always check dominance before declaring success.

---

## Iteration 10: Depth-2 Top-2 (FRONTIER SUCCESS)

**Goal:** Fill the blitz→v1 gap ($3,774 → $5,093 = $1,319 for 6.5x slower)

**Idea:** v1 does depth-2 with top-4 neighbors (16 edge scores). What about top-2? (4 edge scores = 4x faster)

**Results:**
| Agent | $/round | ms/round | Frontier? |
|-------|---------|----------|-----------|
| blitz+nas | $3,709 | 0.0074ms | yes |
| depth2_top2 | $4,472 | 0.0282ms | **YES - NEW!** |
| v1 | $5,051 | 0.0528ms | yes |

**ON FRONTIER:** +$763 more than blitz (3.8x slower), -$579 less than v1 (1.9x faster)

**Why it works:** Depth-2 lookahead captures "buy here, sell there, then what?" information that blitz misses. Top-2 is enough to find good paths without the overhead of top-4.

---

## Iteration 11: Adaptive Early/Late Strategy (FRONTIER SUCCESS)

**Inspiration:** Research into algorithmic trading, multi-armed bandits. Resources deplete over 200 rounds - strategy should adapt.

**Hypothesis:** Early game has abundant resources (explore widely, buy aggressively). Late game has scarce resources (focus on best options).

**Implementation:**
- Rounds 0-100: Check top-4 neighbors, future discount 0.95
- Rounds 100-200: Check top-2 neighbors, future discount 0.80

**Results (50 runs):**
| Agent | $/round | ms/round | Frontier? |
|-------|---------|----------|-----------|
| depth2_top2 | $4,590 | 0.0278ms | yes |
| adaptive | $4,987 | 0.0384ms | **YES - NEW!** |
| champion_v1 | $5,105 | 0.0516ms | yes |

**ON FRONTIER:** +$397 over depth2_top2 for +10.6μs. Fills gap between depth2_top2 and v1.

**Why it works:** Early exploration finds good routes when resources are plentiful. Late focus on best options avoids wasting time on depleted nodes.

---

## Iteration 19: Discount Factor Tuning (v6)

**Hypothesis:** Discount factor for 2-step lookahead scoring affects profit.

**Results:**
| Discount | $/round |
|----------|---------|
| 0.5 | $6,703 |
| 0.7 | $6,757 |
| 0.9 | $6,665 (baseline) |
| 1.0 | $6,595 |

**Finding:** d=0.7 is optimal. Lower discount values immediate profit more, enabling compound gains.

**champion_v6** created with d=0.7. Dominates champion_v5.

---

## Iteration 22: Profile-Guided Optimization

**Tool used:** Python cProfile to identify bottlenecks.

**Finding:** `score_edge` function was 56% of agent execution time (34,758 calls per 200 rounds).

**Optimization:** Inline the hot path, cache world[pos] lookups.

**Results:**
| Agent | Before | After | Speedup |
|-------|--------|-------|---------|
| champion_v6 | 0.095ms | 0.076ms | 1.25x |
| champion_v3 | 0.169ms | 0.156ms | 1.08x |

**Lesson:** Memoization was SLOWER (cache overhead > recomputation). Inlining beats caching when function body is simple.

---

## Iteration 23: Exotic Algorithms (ALL FAILED)

Tested several advanced algorithmic approaches. None beat hand-tuned agents.

| Algorithm | Result | Why Failed |
|-----------|--------|------------|
| Monte Carlo (5 random rollouts) | -$536/r | Random paths worse than greedy best |
| Beam Search (top-3, depth-3) | -$1142/r | Alt paths aren't hidden gems |
| Epsilon-Greedy (10% explore) | -$77/r | Exploration hurts in deterministic env |
| Genetic Algorithm | Dominated by v3 | Found local optimum, not global |
| Inventory-Aware Pathing | +$44/r, +0.004ms | Marginal tradeoff, not dominant |

**Key Insight:** Environment is fully observable and deterministic. Greedy approaches work well. Exotic algorithms add overhead without finding hidden value.

**Numba/Cython:** Not tested (numba not installed). Could still provide speedup via compilation.

---

## Iteration 24: Global-Aware Buy/Sell (FRONTIER SUCCESS)

Applied global price awareness to BOTH buying and selling decisions.

**Hypothesis:** Use price relative to global max to determine sell/buy strategy.

**Strategies tested:**

| Approach | Result vs v6 | Notes |
|----------|--------------|-------|
| adaptive_discount (d varies by opportunity) | -$73/r | Discount tuning doesn't help |
| adaptive_sell (95%/75% thresholds) | +$156/r | Adaptive threshold beats fixed |
| adaptive_depth (depth-3 when weak) | +$11/r | Minor improvement |
| full_adaptive (all combined) | +$88/r | Combination loses vs individual |
| **global_buy_sell** | **+$245/r** | **Weight buying by closeness to global max** |

**Final Configuration (champion_v7):**
1. SELL: At 95%+ of global max unconditionally, or 75%+ if dest is worse
2. BUY: Weight by `margin * closeness` where closeness = buy_price / global_max

**Results:**

| Agent | $/round | ms/round | Efficiency |
|-------|---------|----------|------------|
| champion_v6 | $6,775 | 0.073ms | 93,349 |
| **champion_v7** | **$6,996** | **0.148ms** | **47,320** |

**Pareto Analysis:**
- v7 dominates v3 (higher profit AND similar speed)
- v7 on frontier (highest profit, medium speed)

**Key Insight:** Global price awareness helps both directions:
- Selling: Wait for near-optimal prices, but don't miss good opportunities
- Buying: Prioritize resources we can resell at premium prices

---

## Iteration 25: Cash-Adaptive Thresholds (FRONTIER SUCCESS)

Dynamic thresholds based on cash on hand.

**Hypothesis:** Liquidity constraints matter early, diminish as capital grows.
- Poor: Accept lower-margin deals to build capital
- Rich: Wait for premium prices

**Threshold tuning:**

| Config | Result vs v7 |
|--------|--------------|
| $500-$10000, 70%-95% | +$5/r |
| $500-$10000, 70%-98% | **+$68/r** |
| $500-$10000, 70%-100% | +$65/r |

**Final Configuration (champion_v8):**
- Sell threshold: 70% (poor) → 98% (rich), interpolated by cash
- Cash range: $500 - $10000

**Results:**

| Agent | $/round | ms/round |
|-------|---------|----------|
| champion_v7 | $6,996 | 0.148ms |
| **champion_v8** | **$7,184** | **0.148ms** |

Improvement: +$188/round (+2.7%), same speed.

**Key Insight:** Being pickier when rich (98% vs 95%) is more valuable than being looser when poor.

---

## Iteration 26: Simple Random Agent (FRONTIER SUCCESS)

Fresh approach: What if we abandon lookahead entirely?

**Agent design:**
- Movement: Pure random (no scoring)
- Selling: Everything
- Buying: All profitable items, sorted by ratio

**Results:**

| Agent | $/round | ms/round | Efficiency |
|-------|---------|----------|------------|
| zen_3 | $235 | 0.0020ms | 118,708 |
| **simple_random** | **$1,417** | **0.0021ms** | **664,687** |
| zen_4 | $439 | 0.0024ms | 185,021 |

**Pareto Analysis:**
- Dominates zen_4, zen_5, zen_6
- On frontier between zen_3 and zen_8

**Key Insight:** Random exploration + greedy trading outperforms careful neighbor selection in the ultra-fast tier. The complexity of scoring neighbors costs more time than it saves in quality.

---

## Iteration 27: Precomputed Global Prices (FRONTIER SUCCESS)

Combining simple_random's speed with global price awareness.

**Key insight:** Global prices are static (only quantities change). Precompute once at round 0.

**Agent design:**
- Movement: Pure random
- Selling: Cash-adaptive threshold (60%→95% of global max)
- Buying: All profitable items
- Global prices: Precomputed once at round 0

**Results:**

| Agent | $/round | ms/round | Efficiency |
|-------|---------|----------|------------|
| simple_random | $1,400 | 0.0040ms | 347,750 |
| zen_8 | $1,623 | 0.0048ms | 334,772 |
| **simple_global** | **$2,011** | **0.0029ms** | **689,137** |

**Pareto Analysis:**
- Dominates simple_random (faster AND more profit)
- Dominates zen_8 (faster AND more profit)

**Key Insight:** Precomputing global prices gives cash-adaptive selling benefits without per-round overhead. The combination of random movement + smart selling beats both pure random and zen's careful neighbor selection.

---

## Iteration 28: Hybrid Greedy Movement + Global Selling (FRONTIER SUCCESS)

Combining greedy movement (like blitz) with precomputed global selling.

**Hypothesis:** Random movement in simple_global misses opportunities. Greedy 1-step movement should improve profit without much speed cost.

**Agent design:**
- Movement: Greedy (pick neighbor with best immediate profit potential)
- Selling: Cash-adaptive threshold (60%→95% of global max)
- Buying: All profitable items, sorted by ratio
- Global prices: Precomputed once at round 0

**Results:**

| Agent | $/round | ms/round | Efficiency |
|-------|---------|----------|------------|
| zen_all | $2,710 | 0.0074ms | 363,860 |
| **hybrid_greedy** | **$2,761** | **0.0077ms** | **358,634** |
| blitz | $3,622 | 0.0082ms | 439,690 |

**Pareto Analysis:**
- +$51 more than zen_all for +0.0003ms
- On frontier between zen_all and blitz

**Buy threshold experiment (FAILED):**
- Tested cash-adaptive buy thresholds (5%→35% ROI minimum)
- All configurations hurt performance significantly
- 5%→35% ROI: $313/r (88% loss!)
- 0%→5% ROI: $1,787/r (35% loss)
- Conclusion: Buy everything profitable, no filtering needed

**Key Insight:** Greedy movement helps marginally over random, but the real gains come from global-aware selling. Buy thresholds hurt because they miss profitable opportunities - volume of small trades matters.

---

## Iteration 29: Global Arbitrage (FRONTIER SUCCESS - MASSIVE)

Pure buy-low-sell-high based on global price ratios. No neighbor lookahead.

**Core insight from user:** "If I buy stuff that is super cheap globally, and sell when the node is super expensive globally, then on average I'm going to make great profit."

**Strategy:**
- Buy when current node's sell price <= X% of global max buy price (it's cheap here)
- Sell when current node's buy price >= Y% of global max buy price (it's expensive here)
- Move randomly - over time you encounter both cheap and expensive nodes
- Cash-adaptive thresholds for liquidity management

**Cash-adaptive thresholds:**
- Poor ($<500): buy at <=85% of global, sell at >=65% of global (looser, need turnover)
- Rich ($>10000): buy at <=75% of global, sell at >=85% of global (tighter, wait for deals)

**Threshold tuning:**

| Config | $/round | ms/round | Efficiency |
|--------|---------|----------|------------|
| buy≤90% sell≥60% | $2,372 | 0.0032ms | 741,250 |
| buy≤80% sell≥70% | $3,631 | 0.0030ms | 1,210,333 |
| buy≤80% sell≥75% | $3,819 | 0.0029ms | 1,316,897 |
| **b85→75 s65→85** | **$4,050** | **0.0030ms** | **1,343,195** |

**Results:**

| Agent | $/round | ms/round | Efficiency |
|-------|---------|----------|------------|
| simple_global | $2,028 | 0.0030ms | 676,000 |
| blitz | $3,569 | 0.0077ms | 463,377 |
| **global_arb** | **$4,050** | **0.0030ms** | **1,343,195** |

**Pareto Analysis - DOMINATES:**
- simple_global (same speed, 2x profit!)
- zen_all (faster AND more profit)
- hybrid_greedy (faster AND more profit)
- blitz (faster AND more profit)
- blitz_nas (faster AND more profit)

**Why this works:**
1. Global prices are static - precompute once, use forever
2. No need to look at neighbors - trust statistical arbitrage over 200 rounds
3. Buy low, sell high is the fundamental trading principle
4. Cash-adaptive thresholds optimize for liquidity constraints
5. Random movement is sufficient because you WILL encounter price variations

**Key Insight:** The simplest strategy (buy cheap, sell expensive, move randomly) beats all the sophisticated neighbor-scoring approaches in the fast tier. Complexity was solving the wrong problem.

---

## Ideas Not Yet Tested

- [x] ~~Multi-hop carrying~~ → Partially works! Sell threshold helps, but global buying still broken
- [x] ~~Adaptive depth~~ → Improves on v3 but still worse than v2
- [x] ~~Early termination~~ → Threshold 8000 too aggressive, kills profit
- [x] ~~Alternative scoring~~ → Standard margin×qty is correct
- [x] ~~Tune adaptive threshold~~ → 4000 is optimal (tested 1000-10000)
- [x] ~~Neighbor-aware selling~~ → Helps blitz/v2, hurts v1, conflicts with v3
- [x] ~~Zen variants (neighbor count)~~ → All variants on frontier, fills zen→blitz gap
- [ ] Resource memory (track purchase price, ensure profit on sale)
- [ ] Opponent modeling (avoid nodes where others are heading)
- [ ] Price prediction (resources get depleted, prices might change)
- [ ] Path caching (precompute common routes)
- [ ] Fix v1's limited vision (remove caps?) to enable NAS
- [ ] Combine v3's global threshold WITH NAS?
- [x] ~~Optimize zen_all to match blitz~~ → Random exploration was the key (+$1,200/r!)
- [x] ~~Add NAS to zen variants~~ → Mostly HURTS (see Iteration 8)
- [ ] Hybrid: zen speed with depth-2 scoring (score without full lookahead?)
- [x] ~~Early/late game adaptation~~ → WORKS! See Iteration 11
- [ ] UCB exploration (upper confidence bound for node selection)
- [ ] Route memory (remember profitable paths)
- [ ] Momentum (continue in profitable direction)

---

## Version History

| Version | $/round | ms/round | Efficiency | Key Changes |
|---------|---------|----------|------------|-------------|
| blitz | $3,570 | 0.008ms | 460,975 | 1-step, fastest |
| lookahead | $3,000 | 2ms | 1,500 | 4-step simulation |
| champion_v1 | $5,052 | 0.057ms | 88,632 | depth2 top4 |
| champion_v2 | $6,298 | 0.086ms | 73,398 | depth2 ALL, no cap |
| champion_v3 | $6,875 | 0.161ms | 42,774 | + sell threshold 0.75 (max profit) |
| champion_v4 | $6,284 | 0.118ms | 53,063 | adaptive depth - REGRESSION from v2 |
| **blitz+nas** | **$3,748** | **0.007ms** | **535,429** | **+ neighbor-aware selling (NEW FRONTIER)** |
| **v2+nas** | **$6,668** | **0.087ms** | **76,644** | **+ neighbor-aware selling (DOMINATES v2)** |

**Lessons learned:**
- v3→v4 was optimizing against wrong baseline. Always compare to best, not most recent.
- Test ideas across ALL frontier agents to understand interactions with architecture.

---

## Meta-Cycle Improvements

After each iteration, reflect on the experimental process itself.

### What Worked Well (Iteration 5)

1. **Testing across all frontier agents** revealed that NAS helped blitz/v2 but hurt v1. Without testing all, we'd have wrong conclusions.

2. **Automatic Pareto dominance check** immediately flagged v2 as dominated, preventing us from keeping obsolete agents.

3. **Analyzing WHY** each agent responded differently built understanding:
   - NAS helps agents with good visibility
   - NAS hurts agents with limited vision (can't evaluate carried items)
   - NAS conflicts with existing sell logic

### Hypotheses for Future Meta-Improvements

1. **Prediction before testing**: Before running experiments, write down expected outcome for each variant. Compare predictions to actual results. Wrong predictions reveal gaps in understanding.

2. **Feature decomposition**: When an idea fails on one agent but succeeds on another, identify which architectural feature caused the difference. Creates reusable knowledge.

3. **Confidence intervals**: Current method uses 30-50 runs with same seeds. Should we compute standard deviation and reject results within noise range?

4. **Idea generation systematically**:
   - Look at what frontier agents do differently
   - Ask: "What if we combined X from agent A with Y from agent B?"
   - Ask: "What information is available but unused?"

5. **Time-to-insight tracking**: How long does each iteration take? Are we getting faster at finding improvements?

6. **Failure taxonomy**: Categorize WHY ideas fail:
   - Computational overhead exceeds benefit
   - Conflicts with existing logic
   - Agent architecture can't exploit the idea
   - Idea is just wrong

### What Worked Well (Iteration 7)

1. **Systematic parameter sweep** revealed non-linear relationship between neighbor count and profit. Without testing 3,4,5,6,8,all we'd miss that diminishing returns kick in around 5-6 neighbors.

2. **Factory pattern** in experimental_v6.py made it easy to create and test multiple variants with one code change.

3. **Comparing zen_all vs blitz** revealed that code optimization matters - both check all neighbors but blitz is faster. This opens new optimization avenue.

### Next Iteration Focus

**Option A: Optimize zen_all to match blitz**
- zen_all: $2,710/r @ 0.0074ms
- blitz: $3,622/r @ 0.0082ms
- Both check all neighbors, but blitz is 11% slower yet makes 34% more profit
- Investigate: what does blitz do differently?

**Option B: Add NAS to zen variants**
- NAS helped blitz (+$212) and v2 (+$428) with negligible time cost
- Zen variants have same "check all neighbors" structure as blitz
- Hypothesis: NAS could boost zen variants similarly

**Option C: Close the blitz→v1 gap**
- Current gap: blitz ($3,774) → v1 ($5,093) is $1,319 profit jump for 6.5x slower
- Is there something between them?
