from __future__ import annotations

from functools import lru_cache

import numpy as np
from scipy.special import ndtri


def _cholesky_factor(positions_key: tuple[tuple[float, ...], ...], xi: float) -> np.ndarray:
    """Compute and cache Cholesky factor for a given geometry and xi."""
    positions = np.array(positions_key, dtype=np.float64)
    n = positions.shape[0]
    diff = positions[:, None, :] - positions[None, :, :]
    dist = np.sqrt(np.sum(diff**2, axis=-1))
    corr = np.exp(-dist / xi)
    return np.linalg.cholesky(corr + 1e-12 * np.eye(n))


# Cache by (positions_as_tuple, xi). Maxsize 32 covers any reasonable grid.
@lru_cache(maxsize=32)
def _cached_cholesky(positions_key: tuple[tuple[float, ...], ...], xi: float) -> np.ndarray:
    return _cholesky_factor(positions_key, xi)


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

    # Convert positions to hashable key for caching.
    positions_key = tuple(tuple(row) for row in positions)
    chol = _cached_cholesky(positions_key, xi)
    z = rng.normal(size=(shots, num_qubits)) @ chol.T
    threshold = ndtri(1.0 - p)
    return z > threshold
