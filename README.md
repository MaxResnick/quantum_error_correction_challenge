# qec_benchmark

Open benchmark tooling for decoding surface-code syndromes under spatially correlated noise.

This is a practical benchmark for classical engineers: your job is to build a decoder that beats MWPM when noise is correlated.

## What You Are Building

A decoder that maps syndrome measurements to a logical correction decision.

In this repo, decoders operate on batches:

- Input: `syndrome_array` with shape `(shots, num_detectors)` and binary values
- Output: `np.ndarray` with shape `(shots,)` and binary predictions

The benchmark evaluates logical failure rate and throughput over a grid of parameter points `(L, p, xi)`.

## Why This Benchmark Exists

Under independent noise (`xi = 0`), MWPM performs well.  
Real hardware has correlated noise (crosstalk, bursts, leakage), and MWPM’s iid graph assumptions become wrong.

This benchmark standardizes:

- noise model and parameter grid
- dataset format and splits
- evaluation metrics
- submission API and leaderboard

so results are comparable across decoder approaches.

## Core Concepts (Quick Background)

- **Physical vs logical qubits:** many noisy physical qubits protect one logical qubit.
- **Surface code distance:** for an `L x L` code, distance `d = L`.
- **Syndrome:** stabilizer measurement outcomes indicating local defects.
- **Decoder objective:** infer correction from syndrome while minimizing logical failure.

Correlated noise is parameterized by correlation length `xi`, with covariance:

`C_ij = p * exp(-|i-j| / xi)`

As `xi` increases, clustered errors become more common and iid assumptions degrade.

## Repository Status

Implemented today:

- Phase 1 core: deterministic correlated-noise dataset generation and split packaging
- Phase 2 core: baseline decoders + evaluation harness
- Phase 3 alpha: Docker-isolated submission evaluation + persistent leaderboard records + MVP web UI

## Quickstart (MVP End-to-End)

### 1. Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[server,dev]'
```

### 2. Generate a small local dataset

```bash
qec-benchmark-generate --output data/mvp10_hard --shots 200000 --grid mvp10 --seed 7 --overwrite
```

### 3. Start the local MVP stack

```bash
./scripts/mvp_start.sh
```

Open:

- `http://127.0.0.1:8000/`
- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/leaderboard`
- `http://127.0.0.1:8000/submissions`

### 4. Submit a decoder

```bash
curl -X POST "http://127.0.0.1:8000/submissions/python?name=my_decoder" \
  -F file=@examples/submission_template.py
```

Poll status:

```bash
curl "http://127.0.0.1:8000/submissions/1"
```

### 5. Stop

```bash
./scripts/mvp_stop.sh
```

Run full smoke test:

```bash
./scripts/mvp_smoke_test.sh
```

## CLI Reference

Generate dataset:

```bash
qec-benchmark-generate --output data/mvp10_hard --shots 200000 --grid mvp10 --seed 7
```

Evaluate bundled baselines:

```bash
qec-benchmark-eval --dataset data/mvp10_hard --split public_test --train-split train
```

Run API:

```bash
export QEC_DATASET_DIR=data/mvp10_hard
qec-benchmark-server
```

Run worker:

```bash
export QEC_DATASET_DIR=data/mvp10_hard
qec-benchmark-worker
```

## Decoder Submission Contract

A submission module must define one of:

- `build_decoder(point) -> decoder`
- `build_decoder_family(points) -> dict[ParameterPoint, decoder]`

Each decoder must implement:

- `decode(syndrome_array: np.ndarray) -> np.ndarray`

Minimal template:

```python
from qec_benchmark.baselines import MWPMDecoder

def build_decoder(point):
    return MWPMDecoder(point=point, weighted=True)
```

See [`examples/submission_template.py`](examples/submission_template.py).

## Dataset Format

Generated layout:

```text
<dataset_dir>/
  metadata.json
  train/*.npz
  public_test/*.npz
  private_test/*.npz
```

Each `.npz` contains:

- `syndrome`: `uint8`, shape `(shots, num_detectors)`
- `logical`: `uint8`, shape `(shots,)`

Default benchmark grid:

- `L in {3, 5, 7, 11}`
- `p in {0.001, 0.005, 0.01, 0.02, 0.05}`
- `xi in {0, 1, 2, 5, 10, 20}`

MVP external-testing grid:

- `L = 10`, `p = 0.03`, `xi = 10.0`
- leaderboard rank is based on logical failure rate at this single point

## Built-in Baselines

- `mwpm_uniform`: MWPM graph with uniform edge weights
- `mwpm_iid`: MWPM graph weighted under iid assumption (`p`, ignores `xi`)
- `mlp`: two-layer MLP on syndrome vectors

## Scoring Metrics

Primary metrics tracked in this codebase:

- mean logical failure rate (lower is better)
- mean throughput in syndromes/second (higher is better)

These are reported per submission and per parameter point.

## Runtime and Security Notes

Submission evaluation runs in Docker with:

- network disabled
- read-only root filesystem
- hard timeout
- non-root user
- dropped Linux capabilities + `no-new-privileges`

Useful environment variables:

- `QEC_DOCKER_IMAGE`
- `QEC_DATASET_DIR`
- `QEC_DB_URL`
- `QEC_SUBMISSIONS_DIR`
- `QEC_MAX_SUBMISSION_BYTES`
