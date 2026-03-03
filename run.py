"""CLI entry point: python run.py"""

import argparse
import time

from qec_benchmark import challenge_grid, tiny_grid
from qec_benchmark.config import DEFAULT_SHOTS, DEFAULT_SEED, DEFAULT_TIME_LIMIT, VALIDATE_SEEDS
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
    parser.add_argument(
        "--time-limit", type=float, default=DEFAULT_TIME_LIMIT,
        help=f"seconds per point (default: {DEFAULT_TIME_LIMIT:g})",
    )
    parser.add_argument(
        "--no-time-limit", action="store_true",
        help="disable the per-point time limit",
    )
    parser.add_argument(
        "--validate", action="store_true",
        help="run multiple seeds and report aggregate score",
    )
    args = parser.parse_args()

    from solve import build_decoder

    grid = GRIDS[args.grid]()
    time_limit = None if args.no_time_limit else args.time_limit

    if args.validate:
        _run_validate(build_decoder, grid, args.shots, time_limit)
    else:
        start = time.time()
        result = run_benchmark(
            build_decoder_fn=build_decoder,
            grid=grid,
            shots_per_point=args.shots,
            seed=args.seed,
            time_limit=time_limit,
        )
        elapsed = time.time() - start

        result.print_report(
            shots_per_point=args.shots,
            seed=args.seed,
            elapsed=elapsed,
            time_limit=time_limit,
        )


def _run_validate(build_decoder, grid, shots_per_point, time_limit):
    seeds = VALIDATE_SEEDS
    n_points = len(grid)

    limit_str = f" | {time_limit:g}s limit" if time_limit is not None else ""

    print()
    print(f"  QEC Decoder Benchmark (validate: {len(seeds)} seeds)")
    print(f"  {n_points} points | {shots_per_point:,} shots{limit_str}")
    print()

    scores = []
    total_timed_out = 0
    total_points = 0

    print(f"  Per-seed scores:")
    for seed in seeds:
        result = run_benchmark(
            build_decoder_fn=build_decoder,
            grid=grid,
            shots_per_point=shots_per_point,
            seed=seed,
            time_limit=time_limit,
        )
        scores.append(result.score)
        total_timed_out += result.num_timed_out
        total_points += len(result.point_results)
        print(f"    seed {seed:>5}:  {result.score:>7,} errors/M")

    mean_score = round(sum(scores) / len(scores))

    print()
    print(f"  {'Score':>11}: {mean_score:>10,} errors per million (mean)")
    print(f"  {'Timeouts':>11}: {total_timed_out:>4} / {total_points}")
    print()


if __name__ == "__main__":
    main()
