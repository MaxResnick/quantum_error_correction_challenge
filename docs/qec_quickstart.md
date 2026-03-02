# Overview

This benchmark asks you to build a **classical algorithm** that decodes errors in a quantum error-correcting code.

You do not need to run quantum hardware or know quantum mechanics in depth. In practice, this is a structured prediction task:

- Input: a binary syndrome tensor.
- Output: a binary logical correction decision.

The goal is to beat baseline decoders under **spatially correlated noise**.

## What You Are Actually Building

A function that maps a syndrome to one bit:

$$
\text{decode}(\text{syndrome}) \to \{0,1\}
$$

You win by reducing logical failure rate relative to the baseline, especially when error correlations are strong.

# 1. Bits vs. Qubits

## Classical bits

A classical bit is always `0` or `1`.

## Qubits

A qubit can be in superposition:

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle, \qquad |\alpha|^2 + |\beta|^2 = 1
$$

Measuring collapses the state, so you cannot freely read out quantum information without disturbing it.

## Why this matters for error correction

You cannot copy unknown quantum states (no-cloning theorem), so error detection must be indirect via stabilizer measurements.

# 2. What Quantum Errors Look Like

Single-qubit Pauli errors:

- `X`: bit-flip-like error
- `Z`: phase-flip error
- `Y`: combined bit+phase error

## Depolarizing channel (iid baseline intuition)

$$
\varepsilon(\rho) = (1-p)\rho + \frac{p}{3}(X\rho X + Y\rho Y + Z\rho Z)
$$

## Correlated noise (benchmark focus)

This benchmark uses spatially correlated errors with correlation length $\xi$:

$$
C_{ij} = p \cdot e^{-\lvert i-j \rvert / \xi}
$$

- $\xi=0$: near-independent noise
- larger $\xi$: clustered errors

MWPM assumes independence; this is exactly where it degrades.

# 3. Quantum Error Correction

A logical qubit is encoded across many physical qubits.

- **Physical qubits**: noisy hardware qubits
- **Logical qubit**: protected information

Stabilizers detect local inconsistencies (defects) without directly measuring the logical state.

## Threshold theorem intuition

Below a threshold physical error rate, larger code distance gives rapidly lower logical error:

$$
p_L \sim \left(\frac{p}{p_{\mathrm{th}}}\right)^{(d+1)/2}
$$

where $d$ is code distance.

# 4. Surface Code

For an $L \times L$ surface code in this challenge context:

- encodes one logical qubit
- code distance scales with $L$
- larger $L$ improves robustness but increases decoding cost

A useful parameterization used in docs:

$$
n = 2L^2 - 2L + 1
$$

with one logical qubit encoded.

# 5. Syndromes: Decoder Input

A syndrome is a binary pattern of stabilizer outcomes.

Example decoder contract:

```python
logical_correction = decode(syndrome)  # 0 or 1
```

In multi-round settings you decode a space-time syndrome tensor.

# 6. Baseline: MWPM

Minimum Weight Perfect Matching (MWPM):

1. Build defect graph.
2. Weight edges by an iid likelihood proxy.
3. Solve minimum-weight perfect matching.
4. Convert matches to correction.

It is strong under iid-like regimes and weaker under strong correlations.

# 7. Benchmark Structure

Data is generated with Stim and evaluated on fixed parameter points.

Core metrics:

- **Logical failure rate** (primary, lower is better)
- **Throughput** in syndromes/sec (informational in current MVP)

Current MVP uses a single fixed point for simplicity and comparability.

# 8. Getting Started

Install:

```bash
pip install qec_benchmark
```

Load/evaluate from the package tooling, then submit through the web/API flow.

# 9. Scoring

Leaderboard ordering is based on logical failure rate.

General composite form (longer-term design):

$$
S = 0.7\,(\text{improvement over MWPM}) + 0.3\,\min\!\left(1, \frac{\tau}{10^6}\right)
$$

where $\tau$ is throughput (syndromes/sec).

# Glossary

- **Syndrome**: stabilizer measurement outcomes used by decoder
- **Defect / anyon**: violated stabilizer indicator
- **Code distance**: minimum fault weight causing logical failure
- **MWPM**: minimum-weight perfect matching baseline
- **$\xi$ (xi)**: correlation length in the noise model
