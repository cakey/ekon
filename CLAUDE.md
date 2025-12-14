# Ekon Trading Simulation

A multi-agent trading simulation where agents navigate a graph of nodes, buying and selling resources for profit.

## Project Structure

```
agents/           # Agent implementations
  __init__.py     # Registry of active agents
  champion_*.py   # Current best agents (versioned)
  blitz.py        # Reference: fastest agent
  lookahead.py    # Reference: original best profit
EXPERIMENTS.md    # Knowledge base of tested hypotheses
experiment.py     # Test runner for comparing agents
sim.py            # Main simulation engine
visualizer.py     # Terminal UI for watching simulations
```

## Agent Development Process

### 1. Iterative Refinement
Start simple, add one feature at a time, measure impact:
- Create variants with single parameter changes
- Run `python3 experiment.py 30` to compare
- Each change tells you if that feature is worth it

### 2. Running Experiments
```bash
python3 experiment.py [num_runs]  # Default 30 runs
```
Modify `variants` list in `experiment.py` to test new agents.

### 3. Recording Results
**Always update EXPERIMENTS.md** with:
- What hypothesis you tested
- The delta ($/round and ms/round)
- Verdict: HELPS / HURTS / NO IMPACT
- Why it worked or didn't

### 4. Capturing Winners
When a configuration beats the current champion:
1. Create `agents/champion_vN.py` with full documentation header
2. Include: config, performance metrics, key learnings
3. Register in `agents/__init__.py`
4. Delete experimental files to keep project clean

### 5. Avoiding Wasted Work
Before testing a hypothesis, check EXPERIMENTS.md "Failed Hypotheses" section. Don't retry things that already failed unless you have a specific reason why this time is different.

## Current Best Agent

**champion_v2**: $6,241/round @ 0.094ms
- depth-2 lookahead, ALL neighbors, no quantity cap
- See `agents/champion_v2.py` header for full details

## Key Learnings (Summary)

- More neighbors > more depth (counterintuitive)
- Don't filter or cap - let the algorithm see full potential
- Sorting overhead can exceed pruning benefit
- Global price awareness needs multi-hop carrying to work

## Visualizer

```bash
python3 run_visual.py
```
Controls: SPACE=play/pause, N=step, Q=quit, +/-=speed
