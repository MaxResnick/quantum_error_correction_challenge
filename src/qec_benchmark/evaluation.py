from __future__ import annotations

import time
from dataclasses import asdict, dataclass

import numpy as np

from .baselines import Decoder
from .models import ParameterPoint


@dataclass(frozen=True, slots=True)
class PointResult:
    L: int
    p: float
    xi: float
    shots: int
    logical_failure_rate: float
    throughput_sps: float


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    by_point: dict[str, PointResult]
    mean_failure_rate: float
    mean_throughput_sps: float

    def to_dict(self) -> dict[str, object]:
        return {
            "by_point": {k: asdict(v) for k, v in self.by_point.items()},
            "mean_failure_rate": self.mean_failure_rate,
            "mean_throughput_sps": self.mean_throughput_sps,
        }


def evaluate_decoder(
    *,
    decoder_family: dict[ParameterPoint, Decoder],
    split_data: dict[ParameterPoint, tuple[np.ndarray, np.ndarray]],
) -> EvaluationResult:
    """Evaluate a point-specific decoder family over one benchmark split."""
    point_results: dict[str, PointResult] = {}
    all_failures: list[float] = []
    all_throughputs: list[float] = []

    for point, (syndrome, logical_truth) in split_data.items():
        if point not in decoder_family:
            raise KeyError(f"missing decoder for point {point}")
        decoder = decoder_family[point]

        start = time.perf_counter()
        logical_pred = decoder.decode(syndrome)
        elapsed = max(1e-12, time.perf_counter() - start)

        logical_pred = logical_pred.astype(np.uint8, copy=False).reshape(-1)
        logical_truth = logical_truth.astype(np.uint8, copy=False).reshape(-1)
        if logical_pred.shape != logical_truth.shape:
            raise ValueError(
                f"prediction shape {logical_pred.shape} != truth {logical_truth.shape}"
            )

        failures = float(np.mean(logical_pred != logical_truth))
        throughput = float(syndrome.shape[0] / elapsed)

        result = PointResult(
            L=point.L,
            p=point.p,
            xi=point.xi,
            shots=int(syndrome.shape[0]),
            logical_failure_rate=failures,
            throughput_sps=throughput,
        )
        point_results[point.key()] = result
        all_failures.append(failures)
        all_throughputs.append(throughput)

    return EvaluationResult(
        by_point=point_results,
        mean_failure_rate=float(np.mean(all_failures)) if all_failures else float("nan"),
        mean_throughput_sps=float(np.mean(all_throughputs)) if all_throughputs else float("nan"),
    )
