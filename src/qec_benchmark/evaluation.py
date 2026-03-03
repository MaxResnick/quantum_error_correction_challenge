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
    error_rate: float


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    point_results: list[PointResult]
    total_errors: int
    total_shots: int
    score: int  # errors per million simulations

    def print_table(self, grid_name: str, shots_per_point: int, seed: int) -> None:
        num_points = len(self.point_results)
        print(f"QEC Decoder Benchmark")
        print(
            f"Grid: {grid_name} ({num_points} points) | "
            f"Shots: {shots_per_point:,} | Seed: {seed}"
        )
        print()
        print(f"  {'L':>3}   {'p':<6}   {'xi':<6}   {'Errors':>8}   {'Rate':<10}")
        for r in self.point_results:
            print(
                f"  {r.L:>3}   {r.p:<6.4f}   {r.xi:<6.1f}   {r.errors:>8,}   {r.error_rate:<.6f}"
            )
        print()
        print(f"Total: {self.total_errors:,} errors in {self.total_shots:,} sims")
        print(f"Score: {self.score} errors per million")


def run_benchmark(
    build_decoder_fn: Callable[[ParameterPoint], Decoder],
    grid: list[ParameterPoint],
    shots_per_point: int,
    seed: int,
) -> BenchmarkResult:
    """Generate syndromes on-the-fly, decode, and score."""
    rng = np.random.default_rng(seed)
    point_results: list[PointResult] = []
    total_errors = 0
    total_shots = 0

    for point in grid:
        experiment = SurfaceCodeExperiment(distance=point.L)
        syndromes, logical_truth = experiment.sample_correlated(
            shots=shots_per_point,
            p=point.p,
            xi=point.xi,
            rng=rng,
        )

        decoder = build_decoder_fn(point)
        predictions = decoder.decode(syndromes.astype(np.uint8))
        predictions = predictions.astype(np.uint8).reshape(-1)
        logical_truth = logical_truth.astype(np.uint8).reshape(-1)

        errors = int(np.sum(predictions != logical_truth))
        error_rate = errors / shots_per_point

        point_results.append(
            PointResult(
                L=point.L,
                p=point.p,
                xi=point.xi,
                shots=shots_per_point,
                errors=errors,
                error_rate=error_rate,
            )
        )
        total_errors += errors
        total_shots += shots_per_point

    score = round(total_errors * 1_000_000 / total_shots) if total_shots > 0 else 0

    return BenchmarkResult(
        point_results=point_results,
        total_errors=total_errors,
        total_shots=total_shots,
        score=score,
    )
