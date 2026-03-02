from __future__ import annotations

import argparse
import json

from .baselines import MWPMDecoder, train_mlp_family
from .config import default_grid, mvp10_grid, tiny_grid
from .dataset import generate_dataset, load_split
from .evaluation import evaluate_decoder


def _make_grid(name: str):
    if name == "default":
        return default_grid()
    if name == "tiny":
        return tiny_grid()
    if name == "mvp10":
        return mvp10_grid()
    raise ValueError(f"unknown grid: {name}")


def generate_main() -> None:
    parser = argparse.ArgumentParser(description="Generate qec benchmark dataset")
    parser.add_argument("--output", required=True, help="output dataset directory")
    parser.add_argument("--shots", type=int, default=10000, help="shots per point")
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--rounds", type=int, default=1)
    parser.add_argument("--pauli", type=str, default="X")
    parser.add_argument("--grid", choices=["default", "tiny", "mvp10"], default="tiny")
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    points = _make_grid(args.grid)
    generate_dataset(
        output_dir=args.output,
        points=points,
        shots_per_point=args.shots,
        seed=args.seed,
        rounds=args.rounds,
        pauli=args.pauli,
        overwrite=args.overwrite,
    )
    print(f"Generated dataset at {args.output} ({len(points)} points)")


def eval_main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate built-in qec baseline decoders")
    parser.add_argument("--dataset", required=True, help="dataset root directory")
    parser.add_argument("--split", default="public_test", choices=["train", "public_test", "private_test"])
    parser.add_argument("--train-split", default="train", choices=["train", "public_test", "private_test"])
    parser.add_argument(
        "--baseline",
        default="all",
        choices=["all", "mwpm_uniform", "mwpm_iid", "mlp"],
    )
    args = parser.parse_args()

    eval_split = load_split(args.dataset, args.split)
    train_split = load_split(args.dataset, args.train_split)

    reports: dict[str, dict[str, object]] = {}

    if args.baseline in {"all", "mwpm_uniform"}:
        decoders = {pt: MWPMDecoder(point=pt, weighted=False) for pt in eval_split}
        reports["mwpm_uniform"] = evaluate_decoder(
            decoder_family=decoders,
            split_data=eval_split,
        ).to_dict()

    if args.baseline in {"all", "mwpm_iid"}:
        decoders = {pt: MWPMDecoder(point=pt, weighted=True) for pt in eval_split}
        reports["mwpm_iid"] = evaluate_decoder(
            decoder_family=decoders,
            split_data=eval_split,
        ).to_dict()

    if args.baseline in {"all", "mlp"}:
        mlp_family = train_mlp_family(train_split)
        reports["mlp"] = evaluate_decoder(
            decoder_family=mlp_family,
            split_data=eval_split,
        ).to_dict()

    print(json.dumps(reports, indent=2, sort_keys=True))


if __name__ == "__main__":
    generate_main()
