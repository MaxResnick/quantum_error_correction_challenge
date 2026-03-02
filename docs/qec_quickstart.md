## Overview

This benchmark asks you to build a **classical algorithm** that decodes errors in a quantum error-correcting code.

You do not need to run quantum hardware or understand quantum mechanics at a deep level. In this challenge, you are given binary syndrome measurements from a simulated quantum chip and must output a binary logical correction decision. This document explains the system behind those inputs and outputs so you can make informed algorithmic choices.

## What You Are Actually Building

You are building a function that maps syndrome data to one bit:

$$
\operatorname{decode}(\text{syndrome}) \to \{0,1\}
$$

- Input: a binary syndrome vector (or space-time tensor over repeated rounds).
- Output: a logical correction decision.
- Objective: beat MWPM under spatially correlated noise, especially at large correlation length.

## 1. Bits vs. Qubits

### Classical bits

In classical computing, a bit is always either `0` or `1`. Every register, memory address, and CPU instruction operates on definite bit values.

### Qubits

A qubit can exist in superposition:

$$
|\psi\rangle = \alpha|0\rangle + \beta|1\rangle, \qquad |\alpha|^2 + |\beta|^2 = 1
$$

The amplitudes $\alpha$ and $\beta$ are complex numbers. Measuring the qubit returns `0` with probability $|\alpha|^2$ and `1` with probability $|\beta|^2$, and the state collapses after measurement.

### Why this makes error correction harder

In classical systems, you can copy bits and compare copies. For unknown quantum states, perfect copying is forbidden (no-cloning theorem), so error detection must be indirect. Quantum error correction solves this by encoding one logical qubit across many physical qubits and measuring stabilizers instead of the logical state directly.

## 2. What Quantum Errors Look Like

### Pauli errors

Single-qubit quantum errors are modeled as Pauli operators:

- `X`: bit-flip-like error
- `Z`: phase-flip error
- `Y`: combined bit and phase flip

### Depolarizing channel (iid baseline)

Under independent noise, each qubit fails independently with probability $p$:

$$
\varepsilon(\rho) = (1-p)\rho + \frac{p}{3}\left(X\rho X + Y\rho Y + Z\rho Z\right)
$$

This is the easy regime for decoding.

### Correlated noise (benchmark focus)

Real hardware has spatially correlated faults from effects like cosmic rays, crosstalk, and leakage. The benchmark models this with correlation length $\xi$:

$$
C_{ij} = p \cdot e^{-\lvert i-j \rvert / \xi}
$$

- $\xi = 0$: near-independent errors
- larger $\xi$: stronger clustering

MWPM assumes independent structure in its graph weights; this mismatch is why performance degrades under correlated noise.

## 3. Quantum Error Correction

### Core idea

Encode one **logical qubit** into many noisy **physical qubits**, then repeatedly measure stabilizers to detect faults without collapsing the encoded information.

- Physical qubit: hardware qubit, noisy and fragile.
- Logical qubit: protected virtual qubit used by the computation.

### Threshold theorem intuition

There is a critical physical error rate $p_{\mathrm{th}}$. Below threshold, increasing code distance drives logical failure down rapidly; above threshold, larger codes do not help.

A standard scaling intuition is:

$$
p_L \sim \left(\frac{p}{p_{\mathrm{th}}}\right)^{(d+1)/2}
$$

where $p_L$ is logical failure rate and $d$ is code distance.

## 4. The Surface Code

The surface code is the dominant practical architecture for near-term fault tolerance because it is local in 2D and has efficient decoding in the iid regime.

For an $L \times L$ code in this challenge:

- logical qubits: $k=1$
- distance: $d=L$
- physical qubits:

$$
n = 2L^2 - 2L + 1
$$

So an $L=5$ instance is often written as $[[41,1,5]]$.

### Stabilizers and defects

Two stabilizer families are measured repeatedly:

- Plaquette (`Z`-type) checks
- Vertex (`X`-type) checks

A violated stabilizer (`-1`) is a **defect**. Error chains produce endpoint defects, and decoder quality depends on inferring which defects are paired by the underlying fault process.

### Logical operators and distance

A logical error occurs when actual error plus correction differs by a nontrivial logical operator spanning the lattice. Distance $d$ is the minimum fault weight needed to induce such an undetectable logical failure.

## 5. Syndromes: Decoder Input

A syndrome is the vector of stabilizer outcomes, with `0` meaning no local violation and `1` meaning defect.

```python
syndrome = [0, 0, 1, 0, 1, 0, 0, 1, ...]
logical_correction = decode(syndrome)  # 0 or 1
```

In repeated-round settings, the decoder sees a space-time tensor:

```python
decode(syndrome_tensor) -> int
# syndrome_tensor shape: (rounds, L, L)
```

Measurement faults can create transient defects, which is why temporal context often matters.

## 6. Baseline: MWPM

Minimum Weight Perfect Matching (MWPM) pipeline:

1. Build a defect graph.
2. Connect candidate pairs with weighted edges.
3. Solve minimum-weight perfect matching.
4. Convert matched pairs into correction chains.

Under independent noise, distance-based weights are a good likelihood proxy. Under correlated noise, that proxy is systematically wrong because true likelihood depends on joint spatial structure, not just pairwise shortest paths.

## 7. Benchmark Structure

Dataset generation uses Stim across parameter grids in code size, physical error rate, and correlation length.

Representative grid:

- $L \in \{3,5,7,11\}$
- $p \in \{0.001,0.005,0.01,0.02,0.05\}$
- $\xi \in \{0,1,2,5,10,20\}$

Typical split policy:

- `train`: 80%
- `public-test`: 10%
- `private-test`: 10%

Primary metric is logical failure rate (lower is better), with throughput tracked in syndromes/sec.

### Composite score (long-term design)

$$
S = 0.7\,(\text{improvement over MWPM}) + 0.3\,\min\!\left(1, \frac{\tau}{10^6}\right)
$$

with

$$
\text{improvement} = \frac{p_{\mathrm{MWPM}} - p_{\mathrm{yours}}}{p_{\mathrm{MWPM}}}
$$

where $\tau$ is throughput.

## 8. Getting Started

Install:

```bash
pip install qec_benchmark
```

Load data and evaluate:

```python
from qec_benchmark import load_dataset, evaluate

train_syndromes, train_labels = load_dataset(L=5, p=0.01, xi=5, split="train")
```

Implement decoder:

```python
from qec_benchmark import BaseDecoder

class MyDecoder(BaseDecoder):
    def __init__(self, L, p, xi):
        super().__init__(L, p, xi)

    def train(self, syndromes, labels):
        pass

    def decode(self, syndrome):
        return 0
```

Evaluate:

```python
results = evaluate(MyDecoder, L=5, p=0.01, xi=5)
print(results["logical_failure_rate"])
```

### Practical approaches to try

- Reweighted MWPM using correlation-aware edge costs.
- Belief-propagation or BP+MWPM hybrids.
- Neural decoders over syndrome tensors.
- Renormalization/grouping heuristics.
- Hybrid learned-likelihood + combinatorial decode pipelines.

### Engineering tips

- Use known $(p,\xi)$ at decode time.
- Start with small $L$ for fast iteration.
- Profile inference speed early.
- Spend most effort near threshold-like regimes where MWPM fails hardest.

## 9. Glossary

- **Syndrome**: stabilizer outcome pattern provided to decoder.
- **Defect / anyon**: violated stabilizer indicator.
- **Code distance**: minimum undetectable logical-failure weight.
- **MWPM**: minimum-weight perfect matching decoder baseline.
- **$\xi$**: correlation length controlling spatial error coupling.
- **Logical failure rate**: fraction of instances with incorrect logical correction.
- **Threshold $p_{\mathrm{th}}$**: critical physical error rate for scalable suppression.
