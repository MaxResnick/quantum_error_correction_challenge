from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from qec_benchmark.dataset import generate_dataset
from qec_benchmark.models import ParameterPoint
from qec_benchmark.server import ServerConfig, create_app


def _make_dataset(tmp_path: Path) -> Path:
    dataset_dir = tmp_path / "dataset"
    generate_dataset(
        output_dir=dataset_dir,
        points=[ParameterPoint(L=3, p=0.01, xi=0.0)],
        shots_per_point=50,
        seed=1,
        overwrite=True,
    )
    return dataset_dir


def test_submit_rejects_oversized_file(tmp_path: Path) -> None:
    dataset_dir = _make_dataset(tmp_path)
    app = create_app(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
            submissions_dir=str(tmp_path / "submissions"),
            max_submission_bytes=16,
        )
    )
    client = TestClient(app)

    payload = b"print('this file is too big')\n"
    r = client.post(
        "/submissions/python?name=too-big",
        files={"file": ("submission.py", payload, "text/x-python")},
    )

    assert r.status_code == 413
    assert "submission too large" in r.json()["detail"]
