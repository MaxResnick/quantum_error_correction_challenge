from qec_benchmark.baselines import MWPMDecoder, train_mlp_family
from qec_benchmark.config import tiny_grid
from qec_benchmark.dataset import generate_dataset, load_split
from qec_benchmark.evaluation import evaluate_decoder


def test_baseline_eval_runs(tmp_path) -> None:
    point = tiny_grid()[0]
    out = tmp_path / "dataset"
    generate_dataset(
        output_dir=out,
        points=[point],
        shots_per_point=200,
        seed=11,
        overwrite=True,
    )

    train = load_split(out, "train")
    public = load_split(out, "public_test")

    mwpm_iid = {point: MWPMDecoder(point=point, weighted=True)}
    r1 = evaluate_decoder(decoder_family=mwpm_iid, split_data=public)
    assert 0.0 <= r1.mean_failure_rate <= 1.0
    assert r1.mean_throughput_sps > 0

    mlp = train_mlp_family(train, random_state=0, max_iter=20)
    r2 = evaluate_decoder(decoder_family=mlp, split_data=public)
    assert 0.0 <= r2.mean_failure_rate <= 1.0
    assert r2.mean_throughput_sps > 0
