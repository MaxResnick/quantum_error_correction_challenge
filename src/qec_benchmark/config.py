from __future__ import annotations

from .models import ParameterPoint


def default_grid() -> list[ParameterPoint]:
    Ls = [3, 5, 7, 11]
    ps = [0.001, 0.005, 0.01, 0.02, 0.05]
    xis = [0.0, 1.0, 2.0, 5.0, 10.0, 20.0]
    return [ParameterPoint(L=L, p=p, xi=xi) for L in Ls for p in ps for xi in xis]


def tiny_grid() -> list[ParameterPoint]:
    return [
        ParameterPoint(L=3, p=0.005, xi=0.0),
        ParameterPoint(L=3, p=0.01, xi=2.0),
        ParameterPoint(L=5, p=0.01, xi=5.0),
    ]


def mvp10_grid() -> list[ParameterPoint]:
    # Single-point MVP benchmark: score by logical error rate on 10x10 lattice.
    return [ParameterPoint(L=10, p=0.03, xi=10.0)]
