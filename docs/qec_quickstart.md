# QEC Decoder Benchmark

A Quickstart Guide for Classical Computing Engineers

Everything you need to understand what is being simulated, why it matters,
and how to build a decoder that beats the baseline.

## Overview

This benchmark asks you to build a classical algorithm that decodes errors in a quantum error correcting code. You do not need to run quantum hardware, understand quantum mechanics at a deep level, or work with complex numbers. Everything in this challenge is a classical computational problem — you are given a binary vector of error syndrome measurements and you need to output a binary correction decision. This document explains the physical system behind those inputs and outputs so you can make informed algorithmic choices.

## What you are actually building

A function that takes a binary vector of length ~n and outputs a single bit (0 or 1). The inputs are noisy syndrome measurements from a simulated quantum chip. The output is your prediction of whether a logical error occurred. You win by being right more often than the baseline, especially when errors are spatially correlated.

## 1. Bits vs. Qubits

### Classical bits

In classical computing, a bit is always either 0 or 1. This is the foundation of everything — every register, every memory address, every CPU instruction operates on collections of bits with definite values.

### Qubits

A qubit is the quantum analogue of a bit. The crucial difference is that a qubit can exist in a superposition of 0 and 1 simultaneously. Mathematically, a qubit's state is written as:

$$
|ψ⟩ = α|0⟩ + β|1⟩   where |α|² + |β|² = 1
$$

The values α and β are complex numbers called amplitudes. When you measure the qubit, you get 0 with probability |α|² and 1 with probability |β|², and after measurement the superposition collapses to whichever value you observed. This is the key practical constraint: you cannot simply read out a qubit's state without destroying it.

### Why superposition makes error correction hard

In classical computing, you can copy a bit trivially and check for errors by comparing copies. With qubits this is forbidden by the no-cloning theorem — you cannot make a perfect copy of an unknown quantum state. This means you cannot detect errors the same way. Quantum error correction has to be cleverer: it encodes information redundantly across many qubits and detects errors indirectly, without ever directly reading out the encoded state.

## 2. What Quantum Errors Look Like

### Three kinds of single-qubit errors

Unlike classical bits which can only flip (0→1 or 1→0), qubits can be disturbed in three distinct ways. These are conventionally called Pauli errors after the physicist Wolfgang Pauli:

```text
Classical Computing
Quantum Computing
In This Benchmark
Bit flip (0↔1)
X error (bit flip)
Flips the |0⟩/|1⟩ component
Phase flip (sign change)
Z error (phase flip)
Flips the relative phase of α and β
Both at once
Y error (bit + phase)
Combination of X and Z
```

X errors are the quantum analogue of classical bit flips. Z errors have no classical analogue — they change the phase of the qubit state in a way that has no effect on a direct measurement, but causes problems when the qubit interacts with other qubits. Y errors are simply both X and Z occurring together. In practice all three types occur, and a good error correcting code has to handle all of them.

### The depolarizing noise model

The simplest noise model assumes each physical qubit independently receives a random Pauli error with some probability p. With probability (1-p) nothing happens, and with probability p/3 each of X, Y, Z occurs. This is called the depolarizing channel:

$$
ε(ρ) = (1-p)ρ + (p/3)(XρX + YρY + ZρZ)
$$

The ρ here is the density matrix — a way of representing a quantum state that can also describe statistical mixtures. For our purposes the important thing is just that each qubit fails independently with probability p. This is the easy case. The hard case — the one this benchmark is about — is when errors are correlated across qubits.

### Correlated noise: the hard case

In real hardware, errors are not independent. A cosmic ray hit can cause a cascade of failures across a whole region of the chip. Crosstalk between neighboring qubits means that a gate error on one qubit influences its neighbors. Leakage errors — where a qubit accidentally enters states outside its intended two-level subspace — spread to adjacent qubits through subsequent gate operations.

This benchmark models correlated noise using a spatially correlated error distribution parameterized by a correlation length ξ (Greek letter xi). When ξ = 0 you have independent errors. As ξ increases, errors cluster spatially — a failure at qubit i makes failures at nearby qubits more likely, with the probability decaying exponentially with distance:

$$
C_ij = p · exp(-|i-j| / ξ)
$$

where C_ij is the covariance between errors at qubits i and j

### Why this matters for your decoder

The standard baseline decoder (MWPM) assumes ξ = 0 when it builds its graph. Under correlated noise it is making systematically wrong assumptions. Your job is to build something that uses the known correlation structure to make better decisions.

## 3. Quantum Error Correction

### The core idea

Quantum error correction encodes one logical qubit of information into many physical qubits. The logical qubit is the thing you actually care about — the computation. The physical qubits are the noisy hardware bits that implement it. Spreading the information across many physical qubits means that any individual qubit failure only corrupts part of the encoding, and you can detect and fix it without learning what the encoded information actually is.

The key insight is that you can measure certain collective properties of groups of qubits — called stabilizers — that tell you about errors without revealing the encoded information itself. These measurements are the syndromes that form the input to your decoder.

### Logical vs. physical qubits

#### Physical qubit

An actual qubit on the hardware. Noisy, fragile, subject to X, Y, Z errors at rate p. You have many of these.

#### Logical qubit

The virtual qubit encoded across many physical qubits. This is what the computation uses. It fails only if errors are so widespread that the error correction scheme cannot fix them — a much rarer event.

#### Analogy

Think of RAID storage. You spread data across multiple disks so that any single disk failure is recoverable. The logical storage (what you read and write) is protected even though individual disks (physical storage) can fail. Quantum error correction does the same thing for qubits, but the encoding has to be designed so that error detection never reveals the encoded data.

### The threshold theorem

The most important theoretical result in quantum error correction is the threshold theorem: if the physical error rate p is below a critical value p_threshold, then by using a larger code (more physical qubits per logical qubit) you can make the logical error rate exponentially small. Below threshold, bigger is better. Above threshold, adding more qubits makes things worse because you're accumulating errors faster than you can correct them.

$$
p_L ~ (p / p_threshold)^((d+1)/2)
$$

where p_L is the logical error rate and d is the code distance

The code distance d is roughly the minimum number of physical errors needed to cause an undetectable logical error. A distance-5 code can detect and correct up to 2 errors. For the surface code, p_threshold is approximately 1% under independent noise. Under correlated noise this threshold drops — the open research question is by exactly how much and according to what law.

## 4. The Surface Code

### What it is

The surface code is the leading candidate for fault-tolerant quantum computation on near-term hardware. It has the highest known error threshold of any local code, requires only nearest-neighbor qubit interactions (which maps well to 2D chip architectures), and has an efficient classical decoder in the independent noise case.

An L×L surface code arranges physical qubits on a two-dimensional square lattice. There are two types of qubits:

- Data qubits: These store the encoded information. There are L² of them arranged at the vertices of the lattice.
- Measure qubits: These are used to perform the stabilizer measurements. There are (L²-1) of them, one per stabilizer.

### Key parameters

For an L×L surface code:

- Total physical qubits: n = 2L² - 2L + 1
- Logical qubits encoded: k = 1
- Code distance: d = L
- Can correct up to ⌊(d-1)/2⌋ = ⌊(L-1)/2⌋ arbitrary errors

So L=5 uses 41 physical qubits to protect 1 logical qubit against up to 2 arbitrary errors.

### Stabilizers

A stabilizer is a collective measurement on a group of nearby qubits. There are two types in the surface code:

```text
Classical Computing
Quantum Computing
In This Benchmark
Parity check on 4 bits
Plaquette (Z) stabilizer
Measures ⟨Z⊗Z⊗Z⊗Z⟩ on 4 neighboring data qubits
Another parity check
Vertex (X) stabilizer
Measures ⟨X⊗X⊗X⊗X⟩ on 4 neighboring data qubits
Check result = 0 (no error)
Stabilizer = +1
No detected error in this region
Check result = 1 (error detected)
Stabilizer = -1 (defect)
Error detected — something changed parity
```

Crucially, measuring a stabilizer does not reveal the encoded logical information. It only tells you about errors. This is what makes quantum error correction possible — you can gather information about faults without collapsing the computation.

An X error on a data qubit anticommutes with adjacent Z stabilizers — it flips their measurement outcome from +1 to -1. A Z error anticommutes with adjacent X stabilizers. So different error types leave different patterns of violated stabilizers, which is how the syndrome encodes information about what went wrong.

### Code distance and logical operators

The code distance d = L has a geometric meaning. A logical operator is a string of X or Z gates stretching all the way across the lattice (from one boundary to the opposite boundary). Applying such a string implements a logical X or logical Z gate — it changes the encoded information without being detectable by any stabilizer, because it commutes with all of them.

A logical error occurs when the actual error plus your correction together form such an undetectable logical operator. To cause a logical error undetectably, you need a chain of errors that spans the full lattice — at minimum d = L errors. This is why larger codes (larger L) are more robust.

## 5. Syndromes: The Decoder's Input

### What a syndrome is

After errors occur on data qubits, you measure all stabilizers. The syndrome is the complete list of measurement outcomes — a binary vector of length (n-1) where each bit is 0 (stabilizer measured +1, no local error detected) or 1 (stabilizer measured -1, defect detected). This is the input to your decoder.

```python
# Syndrome: a binary vector, one entry per stabilizer
syndrome = [0, 0, 1, 0, 1, 0, 0, 1, 0, ...]
#               ^       ^       ^
#               defects indicating errors nearby

# Your decoder outputs a single bit:
logical_correction = decode(syndrome)  # 0 or 1
```

### What defects tell you

A single X error on a data qubit flips exactly two adjacent Z stabilizers. So defects always come in pairs — the two endpoints of the error chain that caused them. A lone defect cannot exist; if you see one, there must be another one somewhere else (possibly at the boundary of the lattice, which acts as a virtual defect).

This pairing structure is the geometric foundation of the MWPM decoder: you see a set of defects, and you need to pair them up such that the implied error chains are as short (low probability) as possible.

### Measurement errors

In real hardware, stabilizer measurements themselves can be faulty. A measurement error produces a spurious defect that isn't caused by any data qubit error — it's a false alarm. To handle this, the surface code is typically run for multiple rounds, tracking how the syndrome evolves over time. A real error persists across multiple rounds; a measurement error appears in only one round.

In this benchmark, syndrome data is provided per round. The full input to your decoder is a 3D tensor: two spatial dimensions (the lattice) plus one temporal dimension (rounds of measurement).

### What your function signature looks like

$$
decode(syndrome_tensor) → int
$$

where syndrome_tensor has shape (rounds, L, L) with binary values
and the output is 0 or 1 indicating predicted logical correction

## 6. The Baseline: MWPM

### How MWPM works

Minimum Weight Perfect Matching (MWPM) is the standard decoder. It proceeds in three steps:

- Build a graph. Create a node for each defect. Connect every pair of nodes with an edge. Weight each edge by the probability cost of the error chain that would explain those two defects being partners — under independent noise, this is just the Manhattan distance between them (each step multiplies probability by p).
- Find minimum weight perfect matching. Find the set of edges that pairs up every defect (every node appears in exactly one edge) with minimum total weight. This is the classic Blossom algorithm, running in O(n³) but near-linear in practice with spatial data structures.
- Apply correction. For each matched pair of defects, apply a correction along the shortest path connecting them. Check whether the total correction is a logical operator (i.e., does it span the lattice?) to determine the logical correction bit.

### Where MWPM breaks down

MWPM assigns edge weights assuming errors happen independently — the weight of the path between two defects is just the number of qubits along that path times log(p/(1-p)). This is exactly right under independent noise because the probability of an error chain is just p^length.

Under correlated noise this is wrong. The true probability of an error configuration is not just a function of the length of individual chains — it depends on the joint distribution of all errors. Two error chains that are spatially correlated are collectively more probable than their individual lengths suggest, and MWPM has no way to represent this. It treats each edge independently, which is a structural limitation of the graph representation.

### The opportunity

If you modify the edge weights to reflect the actual correlation structure (or abandon the graph representation entirely in favor of something that captures joint distributions), you can outperform MWPM substantially at high ξ. The question is how to do this efficiently enough to run at the speed required by real hardware.

## 7. The Benchmark Structure

### Dataset

Syndrome samples are pre-generated by simulating the surface code under correlated noise using Stim, a high-performance stabilizer circuit simulator. The dataset spans a grid of parameters:

```text
Classical Computing
Quantum Computing
In This Benchmark
Code size L
3, 5, 7, 11
Larger L = more qubits, higher distance
Error rate p
0.001 to 0.05
Physical error rate per qubit per cycle
Correlation length ξ
0, 1, 2, 5, 10, 20
ξ=0 is independent; ξ=20 is strongly correlated
Samples per point
1,000,000
Split 80/10/10 train/public-test/private-test
```

### Evaluation metric

You are evaluated on logical failure rate — the fraction of test instances where your decoder predicts the wrong logical correction. Lower is better. Results are broken down by (L, p, ξ) so you can see exactly where your decoder performs well and where it degrades.

There is also a speed track. Decoders must run on standardized CPU hardware. Throughput is measured in syndromes decoded per second. A real superconducting quantum processor needs a decoder running at ~1 million syndromes per second to avoid creating a backlog of uncorrected errors.

### Scoring

The composite score rewards both accuracy and speed:

$$
S = 0.7 × (improvement over MWPM) + 0.3 × min(1, throughput / 1M syndromes/sec)
$$

where improvement = (p_MWPM - p_yours) / p_MWPM

## 8. Getting Started

### Install the package

```bash
pip install qec_benchmark
```

```python
# Load data for L=5, p=0.01, xi=5
from qec_benchmark import load_dataset, evaluate

train_syndromes, train_labels = load_dataset(L=5, p=0.01, xi=5, split='train')
# train_syndromes: (800000, rounds, L, L) binary array
# train_labels:    (800000,) binary array — correct logical outcome
```

### Implement a decoder

```python
import numpy as np
from qec_benchmark import BaseDecoder

class MyDecoder(BaseDecoder):
    def __init__(self, L, p, xi):
        super().__init__(L, p, xi)
        # Initialize your model here
        # You know p and xi at init time — use them!

    def train(self, syndromes, labels):
        # Optional: train on the training set
        pass

    def decode(self, syndrome):
        # syndrome: (rounds, L, L) binary numpy array
        # return: 0 or 1
        return 0  # placeholder

# Evaluate against baselines
results = evaluate(MyDecoder, L=5, p=0.01, xi=5)
print(results['logical_failure_rate'])  # vs MWPM baseline
```

### Approaches to try

Here are concrete starting points ordered roughly by complexity:

- Graph reweighting: Modify MWPM edge weights to account for the known correlation structure. If you know ξ, you can compute the true pairwise error probabilities and use them as weights instead of distances. This is the lowest-hanging fruit.
- Belief propagation: Model the syndrome as a factor graph and run message passing to compute marginal error probabilities. Works well on trees; needs cycle-breaking heuristics for the surface code lattice.
- Neural network decoder: Train a CNN or transformer on (syndrome → logical correction) directly. The syndrome tensor has natural spatial structure that CNNs exploit well. You get the correlation structure for free through learned filters.
- Renormalization group: Recursively coarse-grain the syndrome by merging nearby defects. Computationally efficient and handles some correlations naturally through the hierarchy.
- Hybrid approaches: Use a neural network to compute informed edge weights, then feed those into MWPM. You get the theoretical guarantees of the graph-matching framework with learned correlation awareness.

### Tips

- You know ξ and p at decode time. A decoder that ignores this is leaving performance on the table.
- The training set is large and free to generate more of. Stim can produce millions of samples per second. Do not be stingy with training data.
- Profile your decoder. The speed track is real. A decoder that achieves 0.1% lower failure rate but runs 100x slower may score worse overall.
- Start with L=3 or L=5. The smaller codes are easier to overfit and give faster iteration cycles.
- The regime where ξ is large and p is close to the threshold is where MWPM fails hardest and where you have the most to gain.

## 9. Glossary

```text
Classical Computing
Quantum Computing
In This Benchmark
Qubit
A quantum two-level system; can be in superposition of |0⟩ and |1⟩
Pauli error (X/Y/Z)
The three types of single-qubit errors in quantum systems
Stabilizer
A collective measurement on a group of qubits that detects errors without revealing encoded data
Syndrome
The full vector of stabilizer measurement outcomes; your decoder's input
Defect / Anyon
A stabilizer that measured -1 (error detected nearby)
Surface code
A 2D grid error correcting code; the leading fault-tolerant architecture
Code distance d
Minimum errors needed for an undetectable logical failure; d=L for surface code
Logical qubit
The encoded, protected qubit; what the computation actually uses
Physical qubit
The raw, noisy hardware qubit
MWPM
Minimum Weight Perfect Matching; the standard baseline decoder
Correlation length ξ
Controls how far error correlations spread; ξ=0 is independent noise
Logical failure rate
Fraction of decoding instances where the logical correction is wrong; the main metric
Threshold p_th
Max physical error rate below which the code can protect information; depends on ξ
```

For questions, dataset access, and submission instructions, see the benchmark README.
