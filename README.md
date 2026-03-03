# Quantum Error Correction Challenge

Build a decoder that beats minimum-weight perfect matching on correlated noise.

## What is this?

Quantum computers use **surface codes** to protect logical qubits from physical errors. When an error occurs, stabilizer measurements produce a **syndrome** -- a pattern of flags indicating something went wrong. A **decoder** reads the syndrome and decides what correction to apply.

The standard decoder (MWPM) assumes errors are independent. Real hardware has **correlated noise** -- crosstalk, leakage, and burst errors that cluster together. Under correlation, MWPM's assumptions break down and its accuracy degrades.

Your job: build a decoder that handles correlated noise better than MWPM.

## Quick Start

```bash
git clone https://github.com/MaxResnick/quantum_error_correction_challenge.git
cd quantum_error_correction_challenge
uv sync

# Quick test (~5s)
uv run python run.py --grid tiny --shots 1000

# Full benchmark (~60s)
uv run python run.py
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

Your decoder is evaluated across a grid of 24 parameter points:

- **L** in {3, 5, 7} -- code distance, from small to experimental scale
- **p** in {0.005, 0.01} -- physical error rate, below to near threshold
- **xi** in {0, 2, 5, 10} -- correlation length (nearest-neighbor spacing = 2 in stim coordinates)

Total errors across all points, divided by total simulations, scaled to per-million. Default: 1M shots per point, seed 42.

```
uv run python run.py                    # full benchmark (10s/point limit)
uv run python run.py --validate         # multi-seed evaluation (5 seeds)
uv run python run.py --shots 100000     # quick test
uv run python run.py --seed 99          # different seed
uv run python run.py --no-time-limit    # disable time limit (development)
uv run python run.py --grid tiny        # 3-point quick grid
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
- `xi = 2`: mild nearest-neighbor correlation (correlation ~0.37 between adjacent qubits)
- `xi = 5`: moderate multi-qubit clustering
- `xi = 10`: strong correlation (large error bursts spanning much of the lattice)

The copula maps correlated Gaussian samples through the marginal CDF to produce correlated binary errors with the specified marginal rate `p`.

## Rules

- Modify only `solve.py` (200KB max file size, enforced by the arena)
- Your decoder must implement `decode(syndrome_array) -> predictions`
- No filesystem access, no network calls during decoding
- **10-second time limit** per parameter point (covers `build_decoder` + `decode` combined). Exceeding the limit or crashing scores that point as all-wrong
- The arena uses **hidden seeds** -- don't overfit to a specific seed. Use `--validate` to test across multiple seeds
- Your decoder is called once per parameter point with all shots in one batch

## Running Tests

```bash
uv run pytest
```
