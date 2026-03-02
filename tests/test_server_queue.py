from __future__ import annotations

from pathlib import Path

from qec_benchmark.dataset import generate_dataset
from qec_benchmark.evaluation import EvaluationResult, PointResult
from qec_benchmark.models import ParameterPoint
from qec_benchmark.server import BenchmarkServer, EvaluationExecutionError, ServerConfig


def _make_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "dataset"
    generate_dataset(
        output_dir=dataset_dir,
        points=[ParameterPoint(L=3, p=0.01, xi=0.0)],
        shots_per_point=100,
        seed=1,
        overwrite=True,
    )
    return dataset_dir


def _dummy_result() -> EvaluationResult:
    return EvaluationResult(
        by_point={
            "L3_p0.01_xi0": PointResult(
                L=3,
                p=0.01,
                xi=0.0,
                shots=10,
                logical_failure_rate=0.2,
                throughput_sps=999.0,
            )
        },
        mean_failure_rate=0.2,
        mean_throughput_sps=999.0,
    )


def test_queue_submission_lifecycle(tmp_path: Path) -> None:
    dataset_dir = _make_dataset(tmp_path)
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
            job_poll_seconds=0.05,
        )
    )

    submission_path = tmp_path / "submission.py"
    submission_path.write_text("print('stub')\n", encoding="utf-8")

    server._run_submission_in_docker = lambda module_path: (_dummy_result(), "ok")  # type: ignore[method-assign]
    queued = server.enqueue_submission_module(module_path=submission_path, name="queued")

    assert queued.status == "queued"
    assert queued.mean_failure_rate is None

    assert server.run_worker_once() is True
    current = server.get_submission(queued.id)
    assert current.status == "succeeded"
    assert current.mean_failure_rate == 0.2
    assert current.mean_throughput_sps == 999.0
    assert current.runtime_seconds is not None
    assert current.finished_at is not None
    assert current.started_at is not None

    leaderboard = server.leaderboard(track="submission")
    assert len(leaderboard.entries) == 1
    assert leaderboard.entries[0].status == "succeeded"


def test_queue_submission_failure_marks_failed(tmp_path: Path) -> None:
    dataset_dir = _make_dataset(tmp_path)
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
            job_poll_seconds=0.05,
        )
    )

    submission_path = tmp_path / "submission.py"
    submission_path.write_text("print('stub')\n", encoding="utf-8")

    def _raise(module_path):
        raise EvaluationExecutionError("boom", "trace")

    server._run_submission_in_docker = _raise  # type: ignore[method-assign]
    queued = server.enqueue_submission_module(module_path=submission_path, name="queued")
    assert server.run_worker_once() is True

    current = server.get_submission(queued.id)
    assert current.status == "failed"
    assert current.error_message is not None
    assert "boom" in current.error_message
    assert current.log_output == "trace"

    leaderboard = server.leaderboard(track="submission")
    assert len(leaderboard.entries) == 0
