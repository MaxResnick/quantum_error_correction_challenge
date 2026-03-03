import numpy as np

from qec_benchmark.noise import sample_correlated_bernoulli


def _line_positions(n: int) -> np.ndarray:
    """1D positions spaced 1 apart, for simple tests."""
    return np.arange(n, dtype=np.float64).reshape(-1, 1)


def _grid_positions(rows: int, cols: int) -> np.ndarray:
    """2D grid positions."""
    return np.array(
        [(r, c) for r in range(rows) for c in range(cols)], dtype=np.float64
    )


def test_correlated_sampler_deterministic() -> None:
    seed = 1234
    rng1 = np.random.default_rng(seed)
    rng2 = np.random.default_rng(seed)
    pos = _line_positions(16)

    a = sample_correlated_bernoulli(positions=pos, shots=128, p=0.02, xi=5.0, rng=rng1)
    b = sample_correlated_bernoulli(positions=pos, shots=128, p=0.02, xi=5.0, rng=rng2)

    assert a.dtype == np.bool_
    assert a.shape == (128, 16)
    assert np.array_equal(a, b)


def test_independent_limit_matches_marginal() -> None:
    rng = np.random.default_rng(9)
    pos = _line_positions(32)
    x = sample_correlated_bernoulli(positions=pos, shots=20_000, p=0.01, xi=0.0, rng=rng)
    rate = x.mean()
    assert 0.008 < rate < 0.012


def test_2d_positions_work() -> None:
    rng = np.random.default_rng(42)
    pos = _grid_positions(5, 5)
    x = sample_correlated_bernoulli(positions=pos, shots=1000, p=0.05, xi=2.0, rng=rng)
    assert x.shape == (1000, 25)
    assert x.dtype == np.bool_
    rate = x.mean()
    assert 0.02 < rate < 0.08


def test_2d_vs_1d_correlation_differs() -> None:
    """Verify that 2D positions produce different correlation than 1D."""
    seed = 77
    pos_1d = _line_positions(9)
    pos_2d = _grid_positions(3, 3)  # same 9 qubits, but 2D layout

    rng1 = np.random.default_rng(seed)
    a = sample_correlated_bernoulli(positions=pos_1d, shots=5000, p=0.05, xi=2.0, rng=rng1)

    rng2 = np.random.default_rng(seed)
    b = sample_correlated_bernoulli(positions=pos_2d, shots=5000, p=0.05, xi=2.0, rng=rng2)

    # They should differ because the distance matrices are different
    assert not np.array_equal(a, b)
