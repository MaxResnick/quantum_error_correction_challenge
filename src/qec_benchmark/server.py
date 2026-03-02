from __future__ import annotations

import json
import os
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy import JSON, DateTime, Float, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .baselines import MWPMDecoder, train_mlp_family
from .dataset import load_split
from .evaluation import EvaluationResult, PointResult, evaluate_decoder
from .web_ui import render_homepage, render_read_more_page


def _now_utc() -> datetime:
    # Use naive UTC timestamps for SQLite compatibility.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _best_effort_chmod(path: Path, mode: int) -> None:
    try:
        os.chmod(path, mode)
    except OSError:
        # Some filesystems/platforms may not support chmod in the expected way.
        return


class EvaluationExecutionError(Exception):
    def __init__(self, message: str, log_output: str = "", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.log_output = log_output
        self.status_code = status_code


class Base(DeclarativeBase):
    pass


class SubmissionRecord(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    track: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True, default="queued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now_utc)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    runtime_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_failure_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    mean_throughput_sps: Mapped[float | None] = mapped_column(Float, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    submission_path: Mapped[str | None] = mapped_column(String(2000), nullable=True)
    log_output: Mapped[str | None] = mapped_column(String(16000), nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(4000), nullable=True)


class SubmissionResponse(BaseModel):
    id: int
    name: str
    track: str
    status: str
    created_at: datetime
    started_at: datetime | None = None
    heartbeat_at: datetime | None = None
    finished_at: datetime | None = None
    runtime_seconds: float | None = None
    mean_failure_rate: float | None
    mean_throughput_sps: float | None
    log_output: str | None = None
    error_message: str | None = None


class LeaderboardResponse(BaseModel):
    entries: list[SubmissionResponse]


class SubmissionsPageResponse(BaseModel):
    entries: list[SubmissionResponse]
    total: int
    limit: int
    offset: int


class ServerConfig(BaseModel):
    dataset_dir: str
    db_url: str = "sqlite:///qec_benchmark.db"
    docker_image: str = "qec-benchmark-evaluator:latest"
    docker_timeout_seconds: int = 900
    docker_cpus: float = 2.0
    docker_memory: str = "4g"
    docker_pids_limit: int = 256
    docker_user: str = "65532:65532"
    docker_cap_drop_all: bool = True
    docker_no_new_privileges: bool = True
    evaluator_app_dir: str | None = None
    submissions_dir: str = ".qec_submissions"
    job_poll_seconds: float = 0.5
    job_stale_seconds: float = 1800.0
    max_submission_bytes: int = 512 * 1024


class BenchmarkServer:
    def __init__(self, config: ServerConfig):
        self.config = config
        engine_kwargs: dict[str, object] = {"future": True}
        if config.db_url.startswith("sqlite:"):
            engine_kwargs["connect_args"] = {"check_same_thread": False}
        self.engine = create_engine(config.db_url, **engine_kwargs)
        Base.metadata.create_all(self.engine)
        self._dataset_dir = Path(self.config.dataset_dir).resolve()
        self._app_dir = self._resolve_app_dir()
        self._submissions_dir = Path(self.config.submissions_dir).resolve()
        self._submissions_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_app_dir(self) -> Path:
        if self.config.evaluator_app_dir is not None:
            p = Path(self.config.evaluator_app_dir).resolve()
            if not (p / "pyproject.toml").exists():
                raise ValueError(f"evaluator_app_dir missing pyproject.toml: {p}")
            return p

        for parent in Path(__file__).resolve().parents:
            if (parent / "pyproject.toml").exists():
                return parent
        raise ValueError(
            "unable to locate app directory (pyproject.toml). "
            "Set evaluator_app_dir in ServerConfig."
        )

    def _private_split(self):
        try:
            return load_split(self._dataset_dir, "private_test")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def _train_split(self):
        try:
            return load_split(self._dataset_dir, "train")
        except FileNotFoundError as exc:
            raise HTTPException(status_code=500, detail=str(exc)) from exc

    def _persist(self, *, name: str, track: str, result: EvaluationResult) -> SubmissionRecord:
        payload = result.to_dict()
        rec = SubmissionRecord(
            name=name,
            track=track,
            status="succeeded",
            mean_failure_rate=result.mean_failure_rate,
            mean_throughput_sps=result.mean_throughput_sps,
            payload=payload,
            error_message=None,
        )
        with Session(self.engine) as s:
            s.add(rec)
            s.commit()
            s.refresh(rec)
        return rec

    def _to_response(self, rec: SubmissionRecord) -> SubmissionResponse:
        return SubmissionResponse(
            id=rec.id,
            name=rec.name,
            track=rec.track,
            status=rec.status,
            created_at=rec.created_at,
            started_at=rec.started_at,
            heartbeat_at=rec.heartbeat_at,
            finished_at=rec.finished_at,
            runtime_seconds=rec.runtime_seconds,
            mean_failure_rate=rec.mean_failure_rate,
            mean_throughput_sps=rec.mean_throughput_sps,
            log_output=rec.log_output,
            error_message=rec.error_message,
        )

    def evaluate_builtin(self, baseline: str, name: str) -> SubmissionResponse:
        split_data = self._private_split()
        if baseline == "mwpm_uniform":
            decoders = {p: MWPMDecoder(point=p, weighted=False) for p in split_data}
        elif baseline == "mwpm_iid":
            decoders = {p: MWPMDecoder(point=p, weighted=True) for p in split_data}
        elif baseline == "mlp":
            train = self._train_split()
            decoders = train_mlp_family(train)
        else:
            raise HTTPException(status_code=400, detail=f"unknown baseline: {baseline}")

        result = evaluate_decoder(decoder_family=decoders, split_data=split_data)
        rec = self._persist(name=name, track=baseline, result=result)
        return self._to_response(rec)

    def evaluate_submission_module(self, *, module_path: Path, name: str) -> SubmissionResponse:
        try:
            result, log_output = self._run_submission_in_docker(module_path=module_path)
        except EvaluationExecutionError as exc:
            raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

        rec = SubmissionRecord(
            name=name,
            track="submission",
            status="succeeded",
            mean_failure_rate=result.mean_failure_rate,
            mean_throughput_sps=result.mean_throughput_sps,
            payload=result.to_dict(),
            submission_path=str(module_path),
            log_output=log_output,
            error_message=None,
        )
        with Session(self.engine) as s:
            s.add(rec)
            s.commit()
            s.refresh(rec)
        return self._to_response(rec)

    def enqueue_submission_module(self, *, module_path: Path, name: str) -> SubmissionResponse:
        now = _now_utc()
        rec = SubmissionRecord(
            name=name,
            track="submission",
            status="queued",
            created_at=now,
            started_at=None,
            heartbeat_at=None,
            finished_at=None,
            runtime_seconds=None,
            mean_failure_rate=None,
            mean_throughput_sps=None,
            payload=None,
            submission_path=None,
            log_output=None,
            error_message=None,
        )
        with Session(self.engine) as s:
            s.add(rec)
            s.commit()
            s.refresh(rec)
            submission_id = rec.id

        submission_dir = self._submissions_dir / str(submission_id)
        submission_dir.mkdir(parents=True, exist_ok=True)
        worker_input = submission_dir / "submission.py"
        worker_input.write_bytes(module_path.read_bytes())

        with Session(self.engine) as s:
            rec2 = s.get(SubmissionRecord, submission_id)
            if rec2 is not None:
                rec2.submission_path = str(worker_input)
                s.commit()
                s.refresh(rec2)
                return self._to_response(rec2)
        return self._to_response(rec)

    def get_submission(self, submission_id: int) -> SubmissionResponse:
        with Session(self.engine) as s:
            rec = s.get(SubmissionRecord, submission_id)
            if rec is None:
                raise HTTPException(status_code=404, detail=f"submission {submission_id} not found")
            return self._to_response(rec)

    def list_submissions(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        track: str | None = None,
        status: str | None = None,
    ) -> SubmissionsPageResponse:
        if limit <= 0 or limit > 500:
            raise HTTPException(status_code=400, detail="limit must be in [1, 500]")
        if offset < 0:
            raise HTTPException(status_code=400, detail="offset must be >= 0")

        with Session(self.engine) as s:
            query = s.query(SubmissionRecord)
            if track is not None:
                query = query.filter(SubmissionRecord.track == track)
            if status is not None:
                query = query.filter(SubmissionRecord.status == status)

            total = query.count()
            rows = (
                query.order_by(SubmissionRecord.created_at.desc(), SubmissionRecord.id.desc())
                .offset(offset)
                .limit(limit)
                .all()
            )
            entries = [self._to_response(r) for r in rows]

        return SubmissionsPageResponse(
            entries=entries,
            total=total,
            limit=limit,
            offset=offset,
        )

    def claim_next_submission(self) -> int | None:
        now = _now_utc()
        stale_cutoff = now.timestamp() - self.config.job_stale_seconds

        with Session(self.engine) as s:
            # Requeue stale running jobs.
            running = (
                s.query(SubmissionRecord)
                .filter(SubmissionRecord.status == "running")
                .all()
            )
            for rec in running:
                hb = rec.heartbeat_at or rec.started_at or rec.created_at
                if hb.timestamp() < stale_cutoff:
                    rec.status = "queued"
                    rec.started_at = None
                    rec.heartbeat_at = None
                    rec.finished_at = None
                    rec.runtime_seconds = None
                    rec.error_message = "Requeued after stale running job heartbeat timeout"
                    rec.log_output = None

            rec = (
                s.query(SubmissionRecord)
                .filter(SubmissionRecord.status == "queued")
                .order_by(SubmissionRecord.created_at.asc(), SubmissionRecord.id.asc())
                .first()
            )
            if rec is None:
                s.commit()
                return None

            rec.status = "running"
            rec.started_at = now
            rec.heartbeat_at = now
            rec.finished_at = None
            rec.runtime_seconds = None
            rec.error_message = None
            rec.log_output = None
            s.commit()
            return rec.id

    def run_worker_once(self) -> bool:
        submission_id = self.claim_next_submission()
        if submission_id is None:
            return False
        self.process_submission(submission_id)
        return True

    def run_worker_forever(self) -> None:
        while True:
            processed = self.run_worker_once()
            if not processed:
                time.sleep(self.config.job_poll_seconds)

    def process_submission(self, submission_id: int) -> None:
        with Session(self.engine) as s:
            rec = s.get(SubmissionRecord, submission_id)
            if rec is None:
                return
            submission_path = rec.submission_path

        if not submission_path:
            self._set_submission_failed(submission_id, "missing submission_path", "")
            return

        try:
            result, log_output = self._run_submission_in_docker(module_path=Path(submission_path))
        except EvaluationExecutionError as exc:
            self._set_submission_failed(submission_id, exc.message, exc.log_output)
        except Exception as exc:  # noqa: BLE001
            self._set_submission_failed(submission_id, f"{type(exc).__name__}: {exc}", "")
        else:
            self._set_submission_succeeded(submission_id, result, log_output)

    def _run_submission_in_docker(self, *, module_path: Path) -> tuple[EvaluationResult, str]:
        with tempfile.TemporaryDirectory(prefix="qec_eval_") as d:
            temp_dir = Path(d)
            in_path = temp_dir / "submission.py"
            out_path = temp_dir / "result.json"
            _best_effort_chmod(temp_dir, 0o755)
            in_path.write_bytes(module_path.read_bytes())
            _best_effort_chmod(in_path, 0o644)
            # Pre-create output so a non-root container user can write without needing dir write perms.
            out_path.write_text("{}", encoding="utf-8")
            _best_effort_chmod(out_path, 0o666)

            command = self._build_docker_command(input_path=in_path)

            try:
                proc = subprocess.run(
                    command,
                    capture_output=True,
                    text=True,
                    timeout=self.config.docker_timeout_seconds,
                    check=False,
                )
            except FileNotFoundError as exc:
                raise EvaluationExecutionError(
                    "docker binary not found on evaluator host",
                    status_code=503,
                ) from exc
            except subprocess.TimeoutExpired as exc:
                raise EvaluationExecutionError(
                    f"submission evaluation timed out after {self.config.docker_timeout_seconds}s",
                    status_code=408,
                ) from exc

            if proc.returncode != 0:
                stderr_tail = proc.stderr[-4000:] if proc.stderr else ""
                stdout_tail = proc.stdout[-2000:] if proc.stdout else ""
                msg = "submission failed in isolated evaluator"
                details = "\n".join(x for x in [stderr_tail, stdout_tail] if x.strip())
                combined = f"{msg}\n{details}".strip()
                raise EvaluationExecutionError(combined, details)

            if not out_path.exists():
                raise EvaluationExecutionError(
                    "isolated evaluator exited successfully but produced no result.json",
                    status_code=500,
                )

            try:
                payload = json.loads(out_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise EvaluationExecutionError("invalid evaluator output JSON", status_code=500) from exc

            try:
                result = _evaluation_result_from_dict(payload)
            except HTTPException as exc:
                detail = str(exc.detail) if hasattr(exc, "detail") else "invalid evaluator output"
                raise EvaluationExecutionError(detail, status_code=500) from exc
            log_output = "\n".join(x for x in [proc.stderr or "", proc.stdout or ""] if x.strip())[-16000:]
            return result, log_output

    def _build_docker_command(self, *, input_path: Path) -> list[str]:
        input_parent = input_path.parent.resolve()
        dataset_path = self._dataset_dir
        app_path = self._app_dir
        docker_cmd = (
            "PYTHONPATH=/app/src python -m qec_benchmark.submission_runner "
            "--submission /io/submission.py "
            "--dataset /dataset "
            "--split private_test "
            "--output /io/result.json"
        )

        command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "-e",
            "MPLCONFIGDIR=/tmp/mpl",
            "--cpus",
            str(self.config.docker_cpus),
            "--memory",
            self.config.docker_memory,
            "--pids-limit",
            str(self.config.docker_pids_limit),
            "--user",
            self.config.docker_user,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=128m",
        ]
        if self.config.docker_cap_drop_all:
            command.extend(["--cap-drop", "ALL"])
        if self.config.docker_no_new_privileges:
            command.extend(["--security-opt", "no-new-privileges"])
        command.extend(
            [
                "-v",
                f"{app_path}:/app:ro",
                "-v",
                f"{dataset_path}:/dataset:ro",
                "-v",
                f"{input_parent}:/io:rw",
                self.config.docker_image,
                "sh",
                "-lc",
                docker_cmd,
            ]
        )
        return command

    def leaderboard(self, track: str | None = None) -> LeaderboardResponse:
        stmt = select(SubmissionRecord).where(SubmissionRecord.status == "succeeded")
        if track is not None:
            stmt = stmt.where(SubmissionRecord.track == track)
        stmt = stmt.order_by(SubmissionRecord.mean_failure_rate.asc(), SubmissionRecord.id.asc())

        with Session(self.engine) as s:
            rows = list(s.scalars(stmt))
        return LeaderboardResponse(entries=[self._to_response(r) for r in rows])

    def _set_submission_failed(self, submission_id: int, error_message: str, log_output: str) -> None:
        now = _now_utc()
        with Session(self.engine) as s:
            rec = s.get(SubmissionRecord, submission_id)
            if rec is None:
                return
            rec.status = "failed"
            rec.heartbeat_at = now
            rec.finished_at = now
            rec.error_message = error_message[:4000]
            rec.log_output = log_output[-16000:] if log_output else None
            rec.mean_failure_rate = None
            rec.mean_throughput_sps = None
            rec.payload = None
            if rec.started_at is not None:
                rec.runtime_seconds = max(0.0, (now - rec.started_at).total_seconds())
            else:
                rec.runtime_seconds = None
            s.commit()

    def _set_submission_succeeded(
        self,
        submission_id: int,
        result: EvaluationResult,
        log_output: str,
    ) -> None:
        now = _now_utc()
        with Session(self.engine) as s:
            rec = s.get(SubmissionRecord, submission_id)
            if rec is None:
                return
            rec.status = "succeeded"
            rec.heartbeat_at = now
            rec.finished_at = now
            rec.error_message = None
            rec.log_output = log_output[-16000:] if log_output else None
            rec.mean_failure_rate = result.mean_failure_rate
            rec.mean_throughput_sps = result.mean_throughput_sps
            rec.payload = result.to_dict()
            if rec.started_at is not None:
                rec.runtime_seconds = max(0.0, (now - rec.started_at).total_seconds())
            else:
                rec.runtime_seconds = None
            s.commit()


def _evaluation_result_from_dict(payload: dict[str, object]) -> EvaluationResult:
    if not isinstance(payload, dict):
        raise HTTPException(status_code=500, detail="invalid evaluator output payload")

    by_point_raw = payload.get("by_point")
    if not isinstance(by_point_raw, dict):
        raise HTTPException(status_code=500, detail="missing by_point in evaluator output")

    by_point: dict[str, PointResult] = {}
    for key, value in by_point_raw.items():
        if not isinstance(value, dict):
            raise HTTPException(status_code=500, detail=f"invalid point result for {key}")
        try:
            by_point[str(key)] = PointResult(
                L=int(value["L"]),
                p=float(value["p"]),
                xi=float(value["xi"]),
                shots=int(value["shots"]),
                logical_failure_rate=float(value["logical_failure_rate"]),
                throughput_sps=float(value["throughput_sps"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(status_code=500, detail=f"invalid point schema for {key}") from exc

    try:
        mean_failure_rate = float(payload["mean_failure_rate"])
        mean_throughput_sps = float(payload["mean_throughput_sps"])
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(status_code=500, detail="invalid evaluator summary schema") from exc

    return EvaluationResult(
        by_point=by_point,
        mean_failure_rate=mean_failure_rate,
        mean_throughput_sps=mean_throughput_sps,
    )



def create_app(config: ServerConfig | None = None) -> FastAPI:
    if config is None:
        dataset_dir = os.environ.get("QEC_DATASET_DIR", "data/dev")
        db_url = os.environ.get("QEC_DB_URL", "sqlite:///qec_benchmark.db")
        docker_image = os.environ.get("QEC_DOCKER_IMAGE", "qec-benchmark-evaluator:latest")
        submissions_dir = os.environ.get("QEC_SUBMISSIONS_DIR", ".qec_submissions")
        max_submission_bytes = int(os.environ.get("QEC_MAX_SUBMISSION_BYTES", str(512 * 1024)))
        config = ServerConfig(
            dataset_dir=dataset_dir,
            db_url=db_url,
            docker_image=docker_image,
            submissions_dir=submissions_dir,
            max_submission_bytes=max_submission_bytes,
        )

    server = BenchmarkServer(config)
    app = FastAPI(title="QEC Benchmark API", version="0.1.0")

    @app.get("/", response_class=HTMLResponse)
    def homepage() -> str:
        return render_homepage()

    @app.get("/about", response_class=HTMLResponse)
    def about_page() -> str:
        return render_read_more_page()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/leaderboard", response_model=LeaderboardResponse)
    def get_leaderboard(track: str | None = Query(default=None)) -> LeaderboardResponse:
        return server.leaderboard(track=track)

    @app.get("/submissions/{submission_id}", response_model=SubmissionResponse)
    def get_submission(submission_id: int) -> SubmissionResponse:
        return server.get_submission(submission_id=submission_id)

    @app.get("/submissions", response_model=SubmissionsPageResponse)
    def list_submissions(
        limit: int = Query(default=50, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
        track: str | None = Query(default=None),
        status: str | None = Query(default=None),
    ) -> SubmissionsPageResponse:
        return server.list_submissions(limit=limit, offset=offset, track=track, status=status)

    @app.post("/evaluate/baseline", response_model=SubmissionResponse)
    def evaluate_baseline(
        baseline: str = Query(..., pattern="^(mwpm_uniform|mwpm_iid|mlp)$"),
        name: str = Query(default="baseline"),
    ) -> SubmissionResponse:
        return server.evaluate_builtin(baseline=baseline, name=name)

    @app.post("/submissions/python", response_model=SubmissionResponse)
    async def submit_python(
        name: str = Query(default="submission"),
        file: UploadFile = File(...),
    ) -> SubmissionResponse:
        if not file.filename or not file.filename.endswith(".py"):
            raise HTTPException(status_code=400, detail="submission must be a .py file")

        with tempfile.TemporaryDirectory(prefix="qec_submission_") as d:
            path = Path(d) / file.filename
            content = await file.read()
            if len(content) > server.config.max_submission_bytes:
                raise HTTPException(
                    status_code=413,
                    detail=(
                        f"submission too large: {len(content)} bytes "
                        f"(limit {server.config.max_submission_bytes})"
                    ),
                )
            path.write_bytes(content)
            return server.enqueue_submission_module(module_path=path, name=name)

    return app


app = create_app()


def main() -> None:
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
