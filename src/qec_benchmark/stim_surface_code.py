from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pymatching
import stim

from .noise import sample_correlated_bernoulli


def _qubit_targets(inst: stim.CircuitInstruction) -> list[int]:
    out: list[int] = []
    for t in inst.targets_copy():
        if t.is_combiner or t.is_measurement_record_target or t.is_sweep_bit_target:
            continue
        out.append(int(t.value))
    return out


@dataclass(slots=True)
class SurfaceCodeExperiment:
    distance: int
    rounds: int = 1
    pauli: str = "X"
    _circuit: stim.Circuit = field(init=False, repr=False)
    _prefix: stim.Circuit = field(init=False, repr=False)
    _suffix: stim.Circuit = field(init=False, repr=False)
    _data_qubits: np.ndarray = field(init=False, repr=False)

    _data_positions: np.ndarray = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if self.distance < 3:
            raise ValueError("distance must be >=3")
        self.pauli = self.pauli.upper()
        if self.pauli not in {"X", "Y", "Z"}:
            raise ValueError(f"unsupported pauli: {self.pauli}")

        self._circuit = self._build_noiseless_circuit()
        self._prefix, self._suffix = self._split_for_injection(self._circuit)
        self._data_qubits = self._find_data_qubits(self._circuit)
        self._data_positions = self._extract_positions(self._circuit, self._data_qubits)

    def _circuit_name(self) -> str:
        # Use memory_z for X/Y flips, and memory_x for Z flips.
        if self.pauli in {"X", "Y"}:
            return "surface_code:rotated_memory_z"
        return "surface_code:rotated_memory_x"

    def _build_noiseless_circuit(self) -> stim.Circuit:
        return stim.Circuit.generated(
            self._circuit_name(),
            distance=self.distance,
            rounds=self.rounds,
            after_clifford_depolarization=0.0,
            before_round_data_depolarization=0.0,
            before_measure_flip_probability=0.0,
            after_reset_flip_probability=0.0,
        )

    @staticmethod
    def _split_for_injection(circuit: stim.Circuit) -> tuple[stim.Circuit, stim.Circuit]:
        split = None
        for i, inst in enumerate(circuit):
            if inst.name == "TICK":
                split = i + 1
                break
        if split is None:
            raise ValueError("circuit had no TICK; cannot find safe injection point")

        prefix = stim.Circuit()
        suffix = stim.Circuit()
        for i, inst in enumerate(circuit):
            if i < split:
                prefix.append(inst)
            else:
                suffix.append(inst)
        return prefix, suffix

    @staticmethod
    def _find_data_qubits(circuit: stim.Circuit) -> np.ndarray:
        candidates: list[list[int]] = []
        for inst in circuit:
            if inst.name in {"MX", "MY", "MZ", "M"}:
                targets = _qubit_targets(inst)
                if targets:
                    candidates.append(targets)
        if not candidates:
            raise ValueError("could not infer data qubits from measurement instructions")
        # Final data readout is typically the largest measurement block.
        data = max(candidates, key=len)
        return np.asarray(sorted(set(data)), dtype=np.int32)

    @staticmethod
    def _extract_positions(circuit: stim.Circuit, data_qubits: np.ndarray) -> np.ndarray:
        coords = circuit.get_final_qubit_coordinates()
        positions = []
        for q in data_qubits:
            c = coords[int(q)]
            positions.append(c[:2])  # take x, y
        return np.array(positions, dtype=np.float64)

    @property
    def data_positions(self) -> np.ndarray:
        """2D coordinates of data qubits, shape (num_data_qubits, 2)."""
        return self._data_positions

    @property
    def circuit(self) -> stim.Circuit:
        return self._circuit

    @property
    def num_data_qubits(self) -> int:
        return int(self._data_qubits.size)

    @property
    def num_detectors(self) -> int:
        return self._circuit.num_detectors

    def sample_from_mask(self, error_mask: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """Run a batched simulation for a fixed data-qubit error mask.

        Args:
            error_mask: shape=(shots, num_data_qubits), dtype=bool.

        Returns:
            syndromes: shape=(shots, num_detectors), dtype=bool
            logical_flips: shape=(shots,), dtype=bool
        """
        if error_mask.ndim != 2:
            raise ValueError("error_mask must be rank 2")
        shots, width = error_mask.shape
        if width != self.num_data_qubits:
            raise ValueError(
                f"expected width {self.num_data_qubits}, got {width}"
            )

        sim = stim.FlipSimulator(
            batch_size=shots,
            disable_stabilizer_randomization=True,
        )
        sim.do(self._prefix)

        full_mask = np.zeros((self._circuit.num_qubits, shots), dtype=np.bool_)
        full_mask[self._data_qubits, :] = error_mask.T
        sim.broadcast_pauli_errors(pauli=self.pauli, mask=full_mask, p=1.0)

        sim.do(self._suffix)

        syndromes = sim.get_detector_flips().T.astype(np.bool_, copy=False)
        obs = sim.get_observable_flips().T.astype(np.bool_, copy=False)
        if obs.ndim != 2 or obs.shape[1] == 0:
            raise ValueError("expected at least one observable")
        return syndromes, obs[:, 0]

    def sample_correlated(
        self,
        *,
        shots: int,
        p: float,
        xi: float,
        rng: np.random.Generator,
    ) -> tuple[np.ndarray, np.ndarray]:
        mask = sample_correlated_bernoulli(
            positions=self._data_positions,
            shots=shots,
            p=p,
            xi=xi,
            rng=rng,
        )
        return self.sample_from_mask(mask)

    def build_matching(self, *, p: float, weighted: bool) -> pymatching.Matching:
        """Build an MWPM matching graph under an iid assumption.

        The graph always ignores `xi`; this matches the intended baseline tracks.
        """
        iid_circuit = stim.Circuit.generated(
            self._circuit_name(),
            distance=self.distance,
            rounds=self.rounds,
            after_clifford_depolarization=float(p),
        )
        dem = iid_circuit.detector_error_model(decompose_errors=True)
        base = pymatching.Matching.from_detector_error_model(dem)
        if weighted:
            return base

        uniform = pymatching.Matching()
        for n1, n2, data in base.edges():
            fault_ids = data.get("fault_ids", set())
            if n2 is None:
                uniform.add_boundary_edge(int(n1), fault_ids=fault_ids, weight=1.0)
            else:
                uniform.add_edge(int(n1), int(n2), fault_ids=fault_ids, weight=1.0)
        return uniform
