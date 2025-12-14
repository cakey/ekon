# Agent Experiments & Learnings

This document tracks hypotheses tested, results, and learnings to avoid repeating failed experiments.

---

## Experimental Methodology

### Pareto Frontier Validation

When testing a new agent, compare against **all frontier agents**, not just the most recent. An agent is valid if it's on the Pareto frontier - meaning no other agent strictly dominates it on ALL metrics.

**Current Frontier Agents:**
| Agent | $/round | ms/round | Efficiency | Position |
|-------|---------|----------|------------|----------|
| blitz+nas | $3,748 | 0.007ms | 535,429 | fastest |
| v1 | $5,023 | 0.052ms | 96,596 | balanced-fast |
| v2+nas | $6,668 | 0.087ms | 76,644 | balanced (BEST) |
| v3 | $6,823 | 0.168ms | 40,613 | max profit |

*Updated after Iteration 5: blitz+nas replaces blitz, v2+nas dominates v2*

**Validation Rules:**
1. New agent beats at least one frontier agent on at least one metric
2. New agent is NOT strictly dominated (worse on ALL metrics) by any frontier agent
3. If dominated → discard. If on frontier → keep as new option.

**Example:**
- v4 ($6,284/r @ 0.118ms) is dominated by v2 ($6,298/r @ 0.086ms) → DISCARD
- v3 ($6,875/r @ 0.161ms) is not dominated by v2 (more profit) → KEEP

### Experiment Design Process

1. **Identify target**: Which part of the frontier are we trying to improve?
   - More profit than v3? (push right)
   - Faster than blitz? (push left)
   - Better efficiency in the middle? (push up)

2. **Form hypothesis**: What change might achieve this?

3. **Test idea against EACH frontier agent**: Don't just test one variant - apply the idea incrementally to each frontier agent:
   - blitz + idea
   - v1 + idea
   - v2 + idea
   - v3 + idea

4. **Analyze results across all variants**:
   - Did the idea help all agents? Some? None?
   - WHY did it help/hurt in each case?
   - This builds understanding of what the idea actually does

5. **Evaluate position**:
   - On frontier? → New valid option
   - Dominated? → Discard, document why it failed

6. **Update frontier**: Add successful agents, remove any now-dominated agents

### Why Test Against Each Frontier Agent?

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

## Ideas Not Yet Tested

- [x] ~~Multi-hop carrying~~ → Partially works! Sell threshold helps, but global buying still broken
- [x] ~~Adaptive depth~~ → Improves on v3 but still worse than v2
- [x] ~~Early termination~~ → Threshold 8000 too aggressive, kills profit
- [x] ~~Alternative scoring~~ → Standard margin×qty is correct
- [x] ~~Tune adaptive threshold~~ → 4000 is optimal (tested 1000-10000)
- [x] ~~Neighbor-aware selling~~ → Helps blitz/v2, hurts v1, conflicts with v3
- [ ] Resource memory (track purchase price, ensure profit on sale)
- [ ] Opponent modeling (avoid nodes where others are heading)
- [ ] Price prediction (resources get depleted, prices might change)
- [ ] Path caching (precompute common routes)
- [ ] Fix v1's limited vision (remove caps?) to enable NAS
- [ ] Combine v3's global threshold WITH NAS?

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

### Next Iteration Focus

Based on Iteration 5 learnings:
- v1 failed because its limited vision (top-4, qty cap) can't handle carrying items
- **Hypothesis**: Remove v1's caps → might enable NAS benefit
- **Or**: Different idea that works WITH limited vision, not against it
