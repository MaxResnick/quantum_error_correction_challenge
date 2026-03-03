from __future__ import annotations

import numpy as np
from scipy.special import ndtri


def _exp_correlation_matrix(positions: np.ndarray, xi: float) -> np.ndarray:
    """Build correlation matrix from pairwise Euclidean distances.

    Args:
        positions: shape (num_qubits, ndim) -- physical coordinates.
        xi: correlation length. If xi <= 0, returns identity.
    """
    n = positions.shape[0]
    if xi <= 0:
        return np.eye(n, dtype=np.float64)
    diff = positions[:, None, :] - positions[None, :, :]
    dist = np.sqrt(np.sum(diff**2, axis=-1))
    return np.exp(-dist / xi)


def sample_correlated_bernoulli(
    *,
    positions: np.ndarray,
    shots: int,
    p: float,
    xi: float,
    rng: np.random.Generator,
) -> np.ndarray:
    """Sample a correlated Bernoulli field using a Gaussian copula.

    The latent correlation decays exponentially with Euclidean distance
    between qubit positions, with length scale `xi`. For `xi=0`, this
    reduces to independent Bernoulli noise.

    Args:
        positions: shape (num_qubits, ndim) -- physical qubit coordinates.
        shots: number of samples.
        p: marginal error probability per qubit.
        xi: correlation length in the same units as positions.
        rng: numpy random generator.

    Returns:
        Boolean array of shape (shots, num_qubits).
    """
    num_qubits = positions.shape[0]
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

    corr = _exp_correlation_matrix(positions, xi)
    # Add a tiny jitter to stabilize Cholesky for large xi.
    chol = np.linalg.cholesky(corr + 1e-12 * np.eye(num_qubits))
    z = rng.normal(size=(shots, num_qubits)) @ chol.T
    threshold = ndtri(1.0 - p)
    return z > threshold
