from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from fastapi import HTTPException

from qec_benchmark.dataset import generate_dataset
from qec_benchmark.models import ParameterPoint
from qec_benchmark.server import BenchmarkServer, ServerConfig


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


def test_docker_submission_path_persists_result(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_dir = _make_dataset(tmp_path)
    db_path = tmp_path / "submissions.db"
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{db_path}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
        )
    )

    submission_path = tmp_path / "submission.py"
    submission_path.write_text("def build_decoder(point):\n    raise RuntimeError('unused in mock')\n", encoding="utf-8")

    def fake_run(cmd, capture_output, text, timeout, check):
        assert capture_output is True
        assert text is True
        assert check is False
        assert timeout == server.config.docker_timeout_seconds
        assert "--network" in cmd and "none" in cmd
        assert "MPLCONFIGDIR=/tmp/mpl" in cmd
        assert "--read-only" in cmd
        assert "--pids-limit" in cmd
        assert "--user" in cmd and server.config.docker_user in cmd
        assert "--cap-drop" in cmd and "ALL" in cmd
        assert "--security-opt" in cmd and "no-new-privileges" in cmd

        io_mount = None
        for i, token in enumerate(cmd):
            if token == "-v" and i + 1 < len(cmd) and cmd[i + 1].endswith(":/io:rw"):
                io_mount = cmd[i + 1]
                break
        assert io_mount is not None
        host_io = io_mount[: -len(":/io:rw")]

        payload = {
            "by_point": {
                "L3_p0.01_xi0": {
                    "L": 3,
                    "p": 0.01,
                    "xi": 0.0,
                    "shots": 10,
                    "logical_failure_rate": 0.1,
                    "throughput_sps": 12345.0,
                }
            },
            "mean_failure_rate": 0.1,
            "mean_throughput_sps": 12345.0,
        }
        Path(host_io, "result.json").write_text(json.dumps(payload), encoding="utf-8")

        return subprocess.CompletedProcess(cmd, 0, stdout="ok", stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)

    response = server.evaluate_submission_module(module_path=submission_path, name="docker-test")
    assert response.track == "submission"
    assert response.name == "docker-test"
    assert response.mean_failure_rate == 0.1
    assert response.mean_throughput_sps == 12345.0


def test_docker_submission_failure_surfaces_error(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_dir = _make_dataset(tmp_path)
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
        )
    )
    submission_path = tmp_path / "submission.py"
    submission_path.write_text("print('hello')\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        return subprocess.CompletedProcess(args[0], 9, stdout="", stderr="boom")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(HTTPException) as exc:
        server.evaluate_submission_module(module_path=submission_path, name="bad")
    assert exc.value.status_code == 400
    assert "submission failed" in str(exc.value.detail)


def test_docker_missing_binary_returns_503(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dataset_dir = _make_dataset(tmp_path)
    server = BenchmarkServer(
        ServerConfig(
            dataset_dir=str(dataset_dir),
            db_url=f"sqlite:///{tmp_path / 'submissions.db'}",
            evaluator_app_dir=str(Path(__file__).resolve().parents[1]),
        )
    )
    submission_path = tmp_path / "submission.py"
    submission_path.write_text("print('hello')\n", encoding="utf-8")

    def fake_run(*args, **kwargs):
        raise FileNotFoundError("docker")

    monkeypatch.setattr(subprocess, "run", fake_run)

    with pytest.raises(HTTPException) as exc:
        server.evaluate_submission_module(module_path=submission_path, name="bad")
    assert exc.value.status_code == 503
    assert "docker binary not found" in str(exc.value.detail)
