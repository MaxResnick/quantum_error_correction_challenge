from qec_benchmark.config import tiny_grid
from qec_benchmark.dataset import generate_dataset, load_split


def test_dataset_generation_and_load(tmp_path) -> None:
    points = tiny_grid()[:2]
    out = tmp_path / "dataset"
    generate_dataset(
        output_dir=out,
        points=points,
        shots_per_point=120,
        seed=5,
        overwrite=True,
    )

    train = load_split(out, "train")
    public = load_split(out, "public_test")
    private = load_split(out, "private_test")

    assert set(train) == set(points)
    assert set(public) == set(points)
    assert set(private) == set(points)

    for p in points:
        n = train[p][0].shape[0] + public[p][0].shape[0] + private[p][0].shape[0]
        assert n == 120
        assert train[p][0].shape[0] == 96
        assert public[p][0].shape[0] == 12
        assert private[p][0].shape[0] == 12
