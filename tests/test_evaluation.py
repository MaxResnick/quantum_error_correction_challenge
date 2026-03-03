import numpy as np

from qec_benchmark.baselines import MWPMDecoder
from qec_benchmark.config import tiny_grid
from qec_benchmark.evaluation import run_benchmark


def test_run_benchmark_end_to_end() -> None:
    """End-to-end test: generate data, decode, score."""
    grid = tiny_grid()
    result = run_benchmark(
        build_decoder_fn=lambda point: MWPMDecoder(point=point, weighted=True),
        grid=grid,
        shots_per_point=500,
        seed=42,
    )
    assert len(result.point_results) == len(grid)
    assert result.total_shots == 500 * len(grid)
    assert result.total_errors >= 0
    assert result.score >= 0
    for pr in result.point_results:
        assert pr.shots == 500
        assert 0.0 <= pr.error_rate <= 1.0


def test_deterministic_with_same_seed() -> None:
    """Same seed produces identical results."""
    grid = tiny_grid()[:1]
    build = lambda point: MWPMDecoder(point=point, weighted=True)
    r1 = run_benchmark(build, grid, shots_per_point=200, seed=99)
    r2 = run_benchmark(build, grid, shots_per_point=200, seed=99)
    assert r1.total_errors == r2.total_errors
    assert r1.score == r2.score


def test_all_zeros_decoder_worse_than_mwpm() -> None:
    """A decoder that always returns zero should score worse than MWPM."""

    class ZeroDecoder:
        def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
            return np.zeros(syndrome_array.shape[0], dtype=np.uint8)

    grid = tiny_grid()
    mwpm_result = run_benchmark(
        build_decoder_fn=lambda point: MWPMDecoder(point=point, weighted=True),
        grid=grid,
        shots_per_point=1000,
        seed=42,
    )
    zero_result = run_benchmark(
        build_decoder_fn=lambda point: ZeroDecoder(),
        grid=grid,
        shots_per_point=1000,
        seed=42,
    )
    # MWPM should have fewer or equal errors vs a trivial decoder
    assert mwpm_result.total_errors <= zero_result.total_errors
