"""CLI entry point: python run.py"""

import argparse
import time

from qec_benchmark.config import challenge_grid, tiny_grid, DEFAULT_SHOTS, DEFAULT_SEED
from qec_benchmark.evaluation import run_benchmark


GRIDS = {
    "challenge": challenge_grid,
    "tiny": tiny_grid,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="QEC Decoder Benchmark")
    parser.add_argument(
        "--shots", type=int, default=DEFAULT_SHOTS,
        help=f"shots per parameter point (default: {DEFAULT_SHOTS:,})",
    )
    parser.add_argument(
        "--seed", type=int, default=DEFAULT_SEED,
        help=f"RNG seed (default: {DEFAULT_SEED})",
    )
    parser.add_argument(
        "--grid", choices=list(GRIDS.keys()), default="challenge",
        help="parameter grid to use (default: challenge)",
    )
    args = parser.parse_args()

    from solve import build_decoder

    grid = GRIDS[args.grid]()

    start = time.time()
    result = run_benchmark(
        build_decoder_fn=build_decoder,
        grid=grid,
        shots_per_point=args.shots,
        seed=args.seed,
    )
    elapsed = time.time() - start

    result.print_report(
        grid_name=args.grid,
        shots_per_point=args.shots,
        seed=args.seed,
        elapsed=elapsed,
    )


if __name__ == "__main__":
    main()
