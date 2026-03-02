from __future__ import annotations

from pathlib import Path

from qec_benchmark.dataset import generate_dataset
from qec_benchmark.evaluation import EvaluationResult, PointResult
from qec_benchmark.models import ParameterPoint
from qec_benchmark.server import BenchmarkServer, ServerConfig


def _make_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "dataset"
    generate_dataset(
        output_dir=dataset_dir,
        points=[ParameterPoint(L=3, p=0.01, xi=0.0)],
        shots_per_point=60,
        seed=1,
        overwrite=True,
    )
    return dataset_dir


def _dummy_result(v: float) -> EvaluationResult:
    return EvaluationResult(
        by_point={
            "L3_p0.01_xi0": PointResult(
                L=3,
                p=0.01,
                xi=0.0,
                shots=10,
                logical_failure_rate=v,
                throughput_sps=1000.0,
            )
        },
        mean_failure_rate=v,
        mean_throughput_sps=1000.0,
    )


def test_list_submissions_filters_and_pagination(tmp_path: Path) -> None:
    dataset_dir = _make_dataset(tmp_path)
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
            submissions_dir=str(tmp_path / "subs"),
        )
    )

    p1 = tmp_path / "a.py"
    p2 = tmp_path / "b.py"
    p3 = tmp_path / "c.py"
    for p in (p1, p2, p3):
        p.write_text("print('x')\n", encoding="utf-8")

    vals = iter([(_dummy_result(0.1), "ok1"), (_dummy_result(0.2), "ok2")])

    def _runner(module_path):
        if module_path == p3:
            raise Exception("bad")
        return next(vals)

    server._run_submission_in_docker = _runner  # type: ignore[method-assign]

    q1 = server.enqueue_submission_module(module_path=p1, name="one")
    q2 = server.enqueue_submission_module(module_path=p2, name="two")
    q3 = server.enqueue_submission_module(module_path=p3, name="three")

    assert q1.status == "queued"
    assert q2.status == "queued"
    assert q3.status == "queued"

    assert server.run_worker_once() is True
    assert server.run_worker_once() is True
    assert server.run_worker_once() is True

    page = server.list_submissions(limit=10, offset=0)
    assert page.total == 3
    assert len(page.entries) == 3

    failed = server.list_submissions(limit=10, offset=0, status="failed")
    assert failed.total == 1
    assert failed.entries[0].status == "failed"

    succ = server.list_submissions(limit=10, offset=0, status="succeeded")
    assert succ.total == 2

    paged = server.list_submissions(limit=1, offset=1)
    assert paged.total == 3
    assert len(paged.entries) == 1
