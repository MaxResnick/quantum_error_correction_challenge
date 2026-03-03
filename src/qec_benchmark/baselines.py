from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

import numpy as np

from .models import ParameterPoint
from .stim_surface_code import SurfaceCodeExperiment


class Decoder(Protocol):
    def decode(self, syndrome_array: np.ndarray) -> np.ndarray: ...


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
