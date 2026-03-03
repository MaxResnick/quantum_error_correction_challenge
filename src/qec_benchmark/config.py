from __future__ import annotations

from .models import ParameterPoint


def challenge_grid() -> list[ParameterPoint]:
    """The official scoring grid."""
    Ls = [5, 7]
    ps = [0.01]
    xis = [0.0, 5.0, 10.0]
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
