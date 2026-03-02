from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np
from sklearn.neural_network import MLPClassifier

from .models import ParameterPoint
from .stim_surface_code import SurfaceCodeExperiment


class Decoder(Protocol):
    def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
        ...


@dataclass(slots=True)
class MWPMDecoder:
    """Point-specific MWPM decoder."""

    point: ParameterPoint
    weighted: bool
    rounds: int = 1
    pauli: str = "X"
    _experiment: SurfaceCodeExperiment = field(init=False, repr=False)
    _matching: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._experiment = SurfaceCodeExperiment(
            distance=self.point.L,
            rounds=self.rounds,
            pauli=self.pauli,
        )
        self._matching = self._experiment.build_matching(
            p=self.point.p,
            weighted=self.weighted,
        )

    def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
        if syndrome_array.ndim != 2:
            raise ValueError("syndrome_array must be rank 2")
        preds = self._matching.decode_batch(syndrome_array.astype(np.uint8, copy=False))
        if preds.ndim == 2:
            return preds[:, 0].astype(np.uint8, copy=False)
        return preds.astype(np.uint8, copy=False)


@dataclass(slots=True)
class MLPDecoder:
    """A small two-layer MLP baseline trained on one parameter point."""

    hidden_layer_sizes: tuple[int, int] = (128, 64)
    max_iter: int = 50
    random_state: int = 0
    _model: MLPClassifier = field(init=False, repr=False)
    _is_fit: bool = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._model = MLPClassifier(
            hidden_layer_sizes=self.hidden_layer_sizes,
            max_iter=self.max_iter,
            random_state=self.random_state,
            activation="relu",
        )
        self._is_fit = False

    def fit(self, syndrome_array: np.ndarray, logical: np.ndarray) -> None:
        X = syndrome_array.astype(np.float32, copy=False)
        y = logical.astype(np.uint8, copy=False)
        self._model.fit(X, y)
        self._is_fit = True

    def decode(self, syndrome_array: np.ndarray) -> np.ndarray:
        if not self._is_fit:
            raise RuntimeError("MLPDecoder must be fit before decode")
        X = syndrome_array.astype(np.float32, copy=False)
        return self._model.predict(X).astype(np.uint8, copy=False)


def train_mlp_family(
    train_split: dict[ParameterPoint, tuple[np.ndarray, np.ndarray]],
    *,
    random_state: int = 0,
    max_iter: int = 50,
) -> dict[ParameterPoint, MLPDecoder]:
    family: dict[ParameterPoint, MLPDecoder] = {}
    for point, (syndrome, logical) in train_split.items():
        decoder = MLPDecoder(random_state=random_state, max_iter=max_iter)
        decoder.fit(syndrome, logical)
        family[point] = decoder
    return family
