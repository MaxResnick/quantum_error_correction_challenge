"""Minimal submission template for qec_benchmark server."""

from qec_benchmark.baselines import MWPMDecoder


def build_decoder(point):
    # Replace this with your own decoder implementation.
    return MWPMDecoder(point=point, weighted=True)
