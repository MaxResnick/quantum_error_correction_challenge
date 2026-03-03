from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from .baselines import Decoder
from .models import ParameterPoint
from .stim_surface_code import SurfaceCodeExperiment


@dataclass(frozen=True, slots=True)
class PointResult:
    L: int
    p: float
    xi: float
    shots: int
    errors: int

    @property
    def error_rate(self) -> float:
        return self.errors / self.shots if self.shots > 0 else 0.0


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    point_results: list[PointResult]

    @property
    def total_errors(self) -> int:
        return sum(r.errors for r in self.point_results)

    @property
    def total_shots(self) -> int:
        return sum(r.shots for r in self.point_results)

    @property
    def score(self) -> int:
        """Errors per million simulations."""
        ts = self.total_shots
        return round(self.total_errors * 1_000_000 / ts) if ts > 0 else 0

    def _grid_axes(self) -> tuple[list[int], list[float], list[float]]:
        Ls = sorted(set(r.L for r in self.point_results))
        ps = sorted(set(r.p for r in self.point_results))
        xis = sorted(set(r.xi for r in self.point_results))
        return Ls, ps, xis

    def _is_full_grid(self) -> bool:
        Ls, ps, xis = self._grid_axes()
        return len(self.point_results) == len(Ls) * len(ps) * len(xis)

    def print_report(self, shots_per_point: int, seed: int, elapsed: float) -> None:
        n = len(self.point_results)

        print()
        print(f"  QEC Decoder Benchmark")
        print(f"  {n} points | {shots_per_point:,} shots | seed {seed}")
        print()

        if self._is_full_grid() and n > 3:
            self._print_grid_table()
        else:
            self._print_flat_table()

        print()
        print(f"  {'Total':>11}: {self.total_errors:>10,} errors in {self.total_shots:,} shots")
        print(f"  {'Score':>11}: {self.score:>10,} errors per million")
        print(f"  {'Time':>11}: {elapsed:>10.1f}s")
        print()

    def _print_grid_table(self) -> None:
        """Print as grouped L tables with xi columns -- for full grids."""
        Ls, ps, xis = self._grid_axes()
        xi_labels = [f"xi={xi:g}" for xi in xis]
        col_w = max(10, *(len(l) + 2 for l in xi_labels))

        header = f"  {'p':>7}" + "".join(f"{l:>{col_w}}" for l in xi_labels)
        sep = "  " + "─" * len(header)

        lookup = {(r.L, r.p, r.xi): r for r in self.point_results}

        print(f"  Errors per point:")
        for L in Ls:
            print()
            print(f"  L = {L}")
            print(header)
            print(sep)
            for p in ps:
                cells = [f"{lookup[(L, p, xi)].errors:>{col_w},}" for xi in xis]
                print(f"  {p:>7.3f}" + "".join(cells))

    def _print_flat_table(self) -> None:
        """Print as a simple flat table -- for sparse/tiny grids."""
        print(f"  {'L':>5} {'p':>7} {'xi':>6} {'Errors':>10}")
        print(f"  {'─' * 32}")
        for r in self.point_results:
            print(f"  {r.L:>5} {r.p:>7.3f} {r.xi:>6.1f} {r.errors:>10,}")


def run_benchmark(
    build_decoder_fn: Callable[[ParameterPoint], Decoder],
    grid: list[ParameterPoint],
    shots_per_point: int,
    seed: int,
) -> BenchmarkResult:
    """Generate syndromes on-the-fly, decode, and score."""
    rng = np.random.default_rng(seed)
    point_results: list[PointResult] = []

    # Cache experiments by distance (L) since they don't depend on p or xi.
    experiments: dict[int, SurfaceCodeExperiment] = {}

    for point in grid:
        if point.L not in experiments:
            experiments[point.L] = SurfaceCodeExperiment(distance=point.L)
        experiment = experiments[point.L]

        syndromes, logical_truth = experiment.sample_correlated(
            shots=shots_per_point,
            p=point.p,
            xi=point.xi,
            rng=rng,
        )

        decoder = build_decoder_fn(point)
        predictions = decoder.decode(syndromes)

        errors = int(np.sum(predictions.reshape(-1) != logical_truth))

        point_results.append(
            PointResult(
                L=point.L, p=point.p, xi=point.xi,
                shots=shots_per_point, errors=errors,
            )
        )

    return BenchmarkResult(point_results=point_results)
