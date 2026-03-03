from __future__ import annotations

from .models import ParameterPoint


def challenge_grid() -> list[ParameterPoint]:
    """The official scoring grid (24 points).

    Sweeps three axes:
      L  in {3, 5, 7}     -- code distance (small → experimental scale)
      p  in {0.005, 0.01}  -- physical error rate (below threshold → near threshold)
      xi in {0, 2, 5, 10}  -- correlation length in stim coord units
                              (nearest-neighbor spacing = 2)

    xi=0 is the independent-noise baseline where MWPM is strong.
    xi=2 gives nearest-neighbor correlation ~0.37.
    xi=5 gives moderate multi-qubit clustering.
    xi=10 gives strong bursts that span much of the lattice.
    """
    Ls = [3, 5, 7]
    ps = [0.005, 0.01]
    xis = [0.0, 2.0, 5.0, 10.0]
    return [ParameterPoint(L=L, p=p, xi=xi) for L in Ls for p in ps for xi in xis]


def tiny_grid() -> list[ParameterPoint]:
    """A small grid for quick testing."""
    return [
        ParameterPoint(L=3, p=0.005, xi=0.0),
        ParameterPoint(L=3, p=0.01, xi=2.0),
        ParameterPoint(L=5, p=0.01, xi=5.0),
    ]


DEFAULT_SHOTS = 1_000_000
DEFAULT_SEED = 42
DEFAULT_TIME_LIMIT = 2.5  # seconds per point
VALIDATE_SEEDS = [42, 137, 256, 1729, 31415]
