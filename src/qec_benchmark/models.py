from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ParameterPoint:
    """One benchmark configuration point."""

    L: int
    p: float
    xi: float

    def key(self) -> str:
        p_str = format(self.p, ".6g")
        xi_str = format(self.xi, ".6g")
        return f"L{self.L}_p{p_str}_xi{xi_str}"

    @staticmethod
    def from_key(key: str) -> "ParameterPoint":
        # Format: L{L}_p{p}_xi{xi}
        parts = key.split("_")
        if len(parts) != 3:
            raise ValueError(f"invalid parameter key: {key}")
        return ParameterPoint(
            L=int(parts[0][1:]),
            p=float(parts[1][1:]),
            xi=float(parts[2][2:]),
        )


@dataclass(frozen=True, slots=True)
class DatasetSplitFractions:
    train: float = 0.8
    public_test: float = 0.1
    private_test: float = 0.1

    def validate(self) -> None:
        total = self.train + self.public_test + self.private_test
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"split fractions must sum to 1.0, got {total}")
