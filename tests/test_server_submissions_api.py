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
        shots_per_point=40,
        seed=1,
        overwrite=True,
    )
    return dataset_dir


def test_submissions_api_lists_queued_items(tmp_path: Path) -> None:
    dataset_dir = _make_dataset(tmp_path)
    app = create_app(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
            submissions_dir=str(tmp_path / "subs"),
            max_submission_bytes=1024,
        )
    )
    client = TestClient(app)

    payload = b"def build_decoder(point):\n    return None\n"
    r = client.post(
        "/submissions/python?name=queued-api",
        files={"file": ("submission.py", payload, "text/x-python")},
    )
    assert r.status_code == 200

    lst = client.get("/submissions?status=queued").json()
    assert lst["total"] >= 1
    assert any(e["name"] == "queued-api" and e["status"] == "queued" for e in lst["entries"])
