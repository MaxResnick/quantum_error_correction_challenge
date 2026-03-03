import time

import numpy as np

from qec_benchmark.config import tiny_grid
from qec_benchmark.evaluation import run_benchmark


def _slow_decoder_factory(delay: float):
    """Return a build_decoder that sleeps for `delay` seconds during decode."""
    class SlowDecoder:
        def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
            time.sleep(delay)
            return np.zeros(syndrome_array.shape[0], dtype=np.uint8)

    return lambda point: SlowDecoder()


def _crashing_decoder_factory():
    """Return a build_decoder that always raises."""
    class CrashingDecoder:
        def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
            raise RuntimeError("decoder crashed")

    return lambda point: CrashingDecoder()


def test_timeout_scores_all_wrong() -> None:
    """A decoder exceeding the time limit gets max errors (all-wrong)."""
    grid = tiny_grid()[:1]
    shots = 100
    result = run_benchmark(
        build_decoder_fn=_slow_decoder_factory(delay=0.5),
        grid=grid,
        shots_per_point=shots,
        seed=42,
        time_limit=0.1,
    )
    pr = result.point_results[0]
    assert pr.timed_out is True
    assert pr.errors == shots


def test_crashing_decoder_scores_all_wrong() -> None:
    """A decoder that raises gets max errors (all-wrong)."""
    grid = tiny_grid()[:1]
    shots = 100
    result = run_benchmark(
        build_decoder_fn=_crashing_decoder_factory(),
        grid=grid,
        shots_per_point=shots,
        seed=42,
        time_limit=10.0,
    )
    pr = result.point_results[0]
    assert pr.timed_out is True
    assert pr.errors == shots


def test_no_time_limit_allows_anything() -> None:
    """With time_limit=None, slow decoders are not penalized."""
    grid = tiny_grid()[:1]
    shots = 100
    result = run_benchmark(
        build_decoder_fn=_slow_decoder_factory(delay=0.2),
        grid=grid,
        shots_per_point=shots,
        seed=42,
        time_limit=None,
    )
    pr = result.point_results[0]
    assert pr.timed_out is False
    # Zero-decoder won't match all truths, but it shouldn't be all-wrong either
    assert pr.errors < shots
