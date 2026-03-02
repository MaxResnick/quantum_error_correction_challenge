from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path

from .dataset import load_split
from .evaluation import evaluate_decoder
from .models import ParameterPoint


def _build_submission_decoders(module, split_data: dict[ParameterPoint, tuple]) -> dict:
    points = list(split_data.keys())

    if hasattr(module, "build_decoder_family"):
        family = module.build_decoder_family(points)
        if not isinstance(family, dict):
            raise ValueError("build_decoder_family must return dict")
        return family

    if hasattr(module, "build_decoder"):
        return {point: module.build_decoder(point) for point in points}

    raise ValueError("submission must define build_decoder(point) or build_decoder_family(points)")


def run_submission(*, submission_path: Path, dataset_dir: Path, split: str) -> dict[str, object]:
    split_data = load_split(dataset_dir, split)

    spec = importlib.util.spec_from_file_location("qec_submission", submission_path)
    if spec is None or spec.loader is None:
        raise ValueError("unable to load submission module")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    decoders = _build_submission_decoders(module, split_data)
    result = evaluate_decoder(decoder_family=decoders, split_data=split_data)
    return result.to_dict()


def main() -> None:
    parser = argparse.ArgumentParser(description="Run isolated submission evaluation")
    parser.add_argument("--submission", required=True)
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--split", default="private_test", choices=["train", "public_test", "private_test"])
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    result = run_submission(
        submission_path=Path(args.submission),
        dataset_dir=Path(args.dataset),
        split=args.split,
    )

    out = Path(args.output)
    out.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")


if __name__ == "__main__":
    main()
