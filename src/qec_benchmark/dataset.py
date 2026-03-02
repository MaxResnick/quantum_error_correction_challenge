from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np

from .models import DatasetSplitFractions, ParameterPoint
from .stim_surface_code import SurfaceCodeExperiment


def _split_indices(
    shots: int,
    fractions: DatasetSplitFractions,
    rng: np.random.Generator,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    fractions.validate()
    perm = rng.permutation(shots)

    n_train = int(round(shots * fractions.train))
    n_public = int(round(shots * fractions.public_test))
    n_private = shots - n_train - n_public
    if n_private < 0:
        raise ValueError("invalid split sizing")

    train = perm[:n_train]
    public = perm[n_train : n_train + n_public]
    private = perm[n_train + n_public :]
    return train, public, private


def _save_split_file(path: Path, syndrome: np.ndarray, logical: np.ndarray) -> None:
    np.savez_compressed(
        path,
        syndrome=syndrome.astype(np.uint8, copy=False),
        logical=logical.astype(np.uint8, copy=False),
    )


def generate_dataset(
    *,
    output_dir: str | Path,
    points: Iterable[ParameterPoint],
    shots_per_point: int,
    seed: int,
    rounds: int = 1,
    pauli: str = "X",
    split_fractions: DatasetSplitFractions | None = None,
    overwrite: bool = False,
) -> None:
    """Generate a deterministic benchmark dataset on disk.

    Directory layout:
      output_dir/
        metadata.json
        train/{point}.npz
        public_test/{point}.npz
        private_test/{point}.npz
    """
    if shots_per_point <= 0:
        raise ValueError("shots_per_point must be positive")

    split_fractions = split_fractions or DatasetSplitFractions()
    split_fractions.validate()

    out = Path(output_dir)
    if out.exists() and any(out.iterdir()) and not overwrite:
        raise FileExistsError(
            f"output directory {out} is not empty. pass overwrite=True to replace"
        )
    out.mkdir(parents=True, exist_ok=True)

    if overwrite:
        # Remove stale point files from previous generations.
        for split in ("train", "public_test", "private_test"):
            split_dir = out / split
            if split_dir.exists():
                for file in split_dir.glob("*.npz"):
                    file.unlink()
        metadata_path = out / "metadata.json"
        if metadata_path.exists():
            metadata_path.unlink()

    for split in ("train", "public_test", "private_test"):
        (out / split).mkdir(parents=True, exist_ok=True)

    points = list(points)
    master_rng = np.random.default_rng(seed)

    metadata: dict[str, object] = {
        "seed": int(seed),
        "shots_per_point": int(shots_per_point),
        "rounds": int(rounds),
        "pauli": pauli,
        "split_fractions": {
            "train": split_fractions.train,
            "public_test": split_fractions.public_test,
            "private_test": split_fractions.private_test,
        },
        "points": [],
    }

    for point in points:
        point_seed = int(master_rng.integers(0, 2**63 - 1))
        rng = np.random.default_rng(point_seed)

        experiment = SurfaceCodeExperiment(distance=point.L, rounds=rounds, pauli=pauli)
        syndrome, logical = experiment.sample_correlated(
            shots=shots_per_point,
            p=point.p,
            xi=point.xi,
            rng=rng,
        )

        train_idx, public_idx, private_idx = _split_indices(
            shots_per_point,
            split_fractions,
            rng,
        )

        key = point.key()
        _save_split_file(out / "train" / f"{key}.npz", syndrome[train_idx], logical[train_idx])
        _save_split_file(
            out / "public_test" / f"{key}.npz", syndrome[public_idx], logical[public_idx]
        )
        _save_split_file(
            out / "private_test" / f"{key}.npz", syndrome[private_idx], logical[private_idx]
        )

        metadata["points"].append(
            {
                "key": key,
                "L": point.L,
                "p": point.p,
                "xi": point.xi,
                "seed": point_seed,
                "num_detectors": int(syndrome.shape[1]),
            }
        )

    with (out / "metadata.json").open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, sort_keys=True)


def load_split(
    dataset_dir: str | Path,
    split: str,
) -> dict[ParameterPoint, tuple[np.ndarray, np.ndarray]]:
    """Load one dataset split keyed by benchmark parameter point."""
    if split not in {"train", "public_test", "private_test"}:
        raise ValueError(f"invalid split: {split}")

    root = Path(dataset_dir) / split
    if not root.exists():
        raise FileNotFoundError(f"split directory missing: {root}")

    out: dict[ParameterPoint, tuple[np.ndarray, np.ndarray]] = {}
    for file in sorted(root.glob("*.npz")):
        point = ParameterPoint.from_key(file.stem)
        with np.load(file) as data:
            syndrome = data["syndrome"].astype(np.uint8, copy=False)
            logical = data["logical"].astype(np.uint8, copy=False)
        out[point] = (syndrome, logical)
    return out
