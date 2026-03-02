import numpy as np

from qec_benchmark.noise import sample_correlated_bernoulli


def test_correlated_sampler_deterministic() -> None:
    seed = 1234
    rng1 = np.random.default_rng(seed)
    rng2 = np.random.default_rng(seed)

    a = sample_correlated_bernoulli(num_qubits=16, shots=128, p=0.02, xi=5.0, rng=rng1)
    b = sample_correlated_bernoulli(num_qubits=16, shots=128, p=0.02, xi=5.0, rng=rng2)

    assert a.dtype == np.bool_
    assert a.shape == (128, 16)
    assert np.array_equal(a, b)


def test_independent_limit_matches_marginal() -> None:
    rng = np.random.default_rng(9)
    x = sample_correlated_bernoulli(num_qubits=32, shots=20_000, p=0.01, xi=0.0, rng=rng)
    rate = x.mean()
    assert 0.008 < rate < 0.012
