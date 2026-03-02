from __future__ import annotations

import argparse
import os
from pathlib import Path

from .server import BenchmarkServer, ServerConfig


def _load_config_from_env() -> ServerConfig:
    dataset_dir = os.environ.get("QEC_DATASET_DIR", "data/dev")
    db_url = os.environ.get("QEC_DB_URL", "sqlite:///qec_benchmark.db")
    docker_image = os.environ.get("QEC_DOCKER_IMAGE", "qec-benchmark-evaluator:latest")
    submissions_dir = os.environ.get("QEC_SUBMISSIONS_DIR", ".qec_submissions")
    return ServerConfig(
        dataset_dir=dataset_dir,
        db_url=db_url,
        docker_image=docker_image,
        submissions_dir=submissions_dir,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run qec benchmark submission worker")
    parser.add_argument("--once", action="store_true", help="Process at most one queued job")
    parser.add_argument("--poll-seconds", type=float, default=None)
    parser.add_argument("--stale-seconds", type=float, default=None)
    parser.add_argument("--dataset-dir", type=str, default=None)
    parser.add_argument("--db-url", type=str, default=None)
    parser.add_argument("--docker-image", type=str, default=None)
    parser.add_argument("--submissions-dir", type=str, default=None)
    parser.add_argument("--evaluator-app-dir", type=str, default=None)
    args = parser.parse_args()

    config = _load_config_from_env()
    if args.dataset_dir is not None:
        config.dataset_dir = args.dataset_dir
    if args.db_url is not None:
        config.db_url = args.db_url
    if args.docker_image is not None:
        config.docker_image = args.docker_image
    if args.submissions_dir is not None:
        config.submissions_dir = args.submissions_dir
    if args.poll_seconds is not None:
        config.job_poll_seconds = args.poll_seconds
    if args.stale_seconds is not None:
        config.job_stale_seconds = args.stale_seconds
    if args.evaluator_app_dir is not None:
        config.evaluator_app_dir = str(Path(args.evaluator_app_dir).resolve())

    server = BenchmarkServer(config)

    if args.once:
        server.run_worker_once()
        return

    try:
        server.run_worker_forever()
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
