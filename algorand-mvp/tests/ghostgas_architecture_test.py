from utils.constants import BASIS_POINTS, DEFAULT_GAS_POOL_BPS, DEFAULT_PUBLISHER_BPS


def test_default_split_totals() -> None:
    assert DEFAULT_PUBLISHER_BPS + DEFAULT_GAS_POOL_BPS == BASIS_POINTS


def test_basis_points_is_positive() -> None:
    assert BASIS_POINTS > 0
