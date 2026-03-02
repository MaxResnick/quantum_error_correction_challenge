from __future__ import annotations

from pathlib import Path

from qec_benchmark.dataset import generate_dataset
from qec_benchmark.models import ParameterPoint
from qec_benchmark.submission_runner import run_submission


def test_submission_runner_executes_tiny_submission(tmp_path: Path) -> None:
    dataset_dir = tmp_path / "dataset"
    generate_dataset(
        output_dir=dataset_dir,
        points=[ParameterPoint(L=3, p=0.01, xi=0.0)],
        shots_per_point=100,
        seed=3,
        overwrite=True,
    )

    submission = tmp_path / "submission.py"
    submission.write_text(
        "from qec_benchmark.baselines import MWPMDecoder\n"
        "def build_decoder(point):\n"
        "    return MWPMDecoder(point=point, weighted=True)\n",
        encoding="utf-8",
    )

    out = run_submission(
        submission_path=submission,
        dataset_dir=dataset_dir,
        split="private_test",
    )

    assert "by_point" in out
    assert "mean_failure_rate" in out
    assert "mean_throughput_sps" in out
    assert len(out["by_point"]) == 1
