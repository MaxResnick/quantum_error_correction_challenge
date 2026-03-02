from __future__ import annotations

import numpy as np
from scipy.special import ndtri


def _exp_correlation_matrix(num_qubits: int, xi: float) -> np.ndarray:
    if num_qubits <= 0:
        raise ValueError("num_qubits must be positive")
    if xi <= 0:
        return np.eye(num_qubits, dtype=np.float64)
    idx = np.arange(num_qubits, dtype=np.float64)
    d = np.abs(idx[:, None] - idx[None, :])
    return np.exp(-d / xi)


def sample_correlated_bernoulli(
    *,
    num_qubits: int,
    shots: int,
    p: float,
    xi: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample a correlated Bernoulli field using a Gaussian copula.

    The latent correlation decays exponentially with distance scale `xi`. For
    `xi=0`, this reduces to independent Bernoulli noise.
    """
    if not (0.0 <= p <= 1.0):
        raise ValueError(f"p must be in [0, 1], got {p}")
    if shots < 0:
        raise ValueError(f"shots must be non-negative, got {shots}")
    if shots == 0:
        return np.zeros((0, num_qubits), dtype=np.bool_)
    if p == 0.0:
        return np.zeros((shots, num_qubits), dtype=np.bool_)
    if p == 1.0:
        return np.ones((shots, num_qubits), dtype=np.bool_)

    if xi <= 0:
        return rng.random((shots, num_qubits)) < p

    corr = _exp_correlation_matrix(num_qubits, xi)
    # Add a tiny jitter to stabilize Cholesky for large xi.
    chol = np.linalg.cholesky(corr + 1e-12 * np.eye(num_qubits))
    z = rng.normal(size=(shots, num_qubits)) @ chol.T
    threshold = ndtri(1.0 - p)
    return z > threshold
