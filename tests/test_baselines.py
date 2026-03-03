from qec_benchmark.baselines import MWPMDecoder
from qec_benchmark.config import tiny_grid
from qec_benchmark.evaluation import run_benchmark


def _mwpm(point):
    return MWPMDecoder(point=point, weighted=True)


def test_mwpm_baseline_runs() -> None:
    grid = tiny_grid()[:1]
    result = run_benchmark(build_decoder_fn=_mwpm, grid=grid, shots_per_point=200, seed=11)
    assert len(result.point_results) == 1
    pr = result.point_results[0]
    assert 0.0 <= pr.error_rate <= 1.0
    assert pr.errors >= 0
    assert result.total_shots == 200
