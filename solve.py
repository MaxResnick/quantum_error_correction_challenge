"""Your decoder implementation. Modify this file to beat the baseline."""

from qec_benchmark.baselines import MWPMDecoder
from qec_benchmark.models import ParameterPoint


def build_decoder(point: ParameterPoint):
    """Return a decoder for the given parameter point.

    Your decoder must implement: decode(syndrome_array: np.ndarray) -> np.ndarray
    where syndrome_array is (shots, num_detectors) uint8 and return is (shots,) uint8.
    """
    return MWPMDecoder(point=point, weighted=True)
