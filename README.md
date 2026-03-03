# Quantum Error Correction Challenge

Build a decoder that beats minimum-weight perfect matching on correlated noise.

## What is this?

Quantum computers use **surface codes** to protect logical qubits from physical errors. When an error occurs, stabilizer measurements produce a **syndrome** -- a pattern of flags indicating something went wrong. A **decoder** reads the syndrome and decides what correction to apply.

The standard decoder (MWPM) assumes errors are independent. Real hardware has **correlated noise** -- crosstalk, leakage, and burst errors that cluster together. Under correlation, MWPM's assumptions break down and its accuracy degrades.

Your job: build a decoder that handles correlated noise better than MWPM.

## Quick Start

```bash
git clone https://github.com/benedictbrady/quantum-error-correction-challenge.git
cd quantum-error-correction-challenge
python3 -m venv .venv && source .venv/bin/activate
pip install -e .

# Quick test (~5s)
python run.py --grid tiny --shots 1000

# Full benchmark (~60s)
python run.py
```

## How it works

Edit **`solve.py`**. That's the only file you need to change.

```python
def build_decoder(point: ParameterPoint):
    """Return a decoder for the given parameter point."""
    return MWPMDecoder(point=point, weighted=True)  # <- replace this
```

Your decoder receives a batch of syndromes and returns predictions:

- **Input**: `syndrome_array` -- shape `(shots, num_detectors)`, dtype `uint8`, binary values
- **Output**: `np.ndarray` -- shape `(shots,)`, dtype `uint8`, binary predictions (0 or 1)

Each prediction is whether a logical flip occurred. The benchmark generates fresh data from a seed on every run -- no pre-generated datasets, no data files.

The `point` parameter tells you the current configuration:

- `point.L` -- lattice size (code distance)
- `point.p` -- physical error rate
- `point.xi` -- correlation length (0 = independent noise)

## Scoring

**Errors per million simulations** (integer, lower is better).

Your decoder is evaluated across a grid of 6 parameter points:

| L | p    | xi   |
|---|------|------|
| 5 | 0.01 | 0.0  |
| 5 | 0.01 | 5.0  |
| 5 | 0.01 | 10.0 |
| 7 | 0.01 | 0.0  |
| 7 | 0.01 | 5.0  |
| 7 | 0.01 | 10.0 |

Total errors across all points, divided by total simulations, scaled to per-million. Default: 1M shots per point, seed 42.

```
python run.py                    # full benchmark
python run.py --shots 100000     # quick test
python run.py --seed 99          # different seed
python run.py --grid tiny        # 3-point quick grid
```

## The Baseline

The default decoder is **Minimum-Weight Perfect Matching (MWPM)**. It builds a graph from the detector error model assuming independent noise, then finds the minimum-weight matching to determine corrections.

MWPM is near-optimal for independent noise (`xi = 0`). But as correlation length `xi` increases, errors cluster together. MWPM doesn't know about this clustering -- it still assumes every error is independent -- so it makes worse decisions. The gap between MWPM and an ideal correlated-noise decoder grows with `xi`.

## The Noise Model

Errors are generated via a **Gaussian copula** with exponentially decaying correlation:

```
C_ij = exp(-|i - j| / xi)
```

- `xi = 0`: independent Bernoulli noise (MWPM is strong here)
- `xi = 5`: moderate correlation (errors tend to cluster)
- `xi = 10`: strong correlation (large error bursts, MWPM struggles)

The copula maps correlated Gaussian samples through the marginal CDF to produce correlated binary errors with the specified marginal rate `p`.

## Hints

- Look at how MWPM fails: at high `xi`, correlated error bursts fool the independent-noise graph weights
- The syndrome itself contains spatial structure that reveals correlation patterns
- You can build different decoders for different parameter points
- Consider combining MWPM with a learned correction layer
- Neural decoders, belief propagation, or hybrid approaches could all work
- You have access to unlimited training data via `SurfaceCodeExperiment.sample_correlated()`

## Rules

- Modify only `solve.py`
- Your decoder must implement `decode(syndrome_array) -> predictions`
- No filesystem access, no network calls during decoding
- Scoring uses seed 42 -- don't overfit to a specific seed
- Your decoder is called once per parameter point with all shots in one batch

## Running Tests

```bash
pytest
```
