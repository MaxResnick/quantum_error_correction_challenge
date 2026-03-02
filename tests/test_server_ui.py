from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from qec_benchmark.server import ServerConfig, create_app


def test_homepage_renders(tmp_path: Path) -> None:
    app = create_app(
        ServerConfig(
            dataset_dir=str(tmp_path / "dataset"),
            db_url=f"sqlite:///{tmp_path / 'ui.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
        )
    )
    client = TestClient(app)

    res = client.get("/")
    assert res.status_code == 200
    assert "Quantum Error Correction" in res.text
    assert "POST /submissions/python" in res.text
    assert 'href="/about"' in res.text


def test_read_more_about_page_renders(tmp_path: Path) -> None:
    app = create_app(
        ServerConfig(
            dataset_dir=str(tmp_path / "dataset"),
            db_url=f"sqlite:///{tmp_path / 'ui_about.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
        )
    )
    client = TestClient(app)

    res = client.get("/about")
    assert res.status_code == 200
    assert "Overview" in res.text
    assert "What you are actually building" in res.text
