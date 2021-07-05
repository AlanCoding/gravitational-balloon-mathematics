import pytest

from gb import inflation
from gb.ported import gravity as old_inflation

from gb.constants import rho


ACCEPTANCE = 1.0e-9


def assert_acceptable(new, old):
    assert abs(new - old) / old < ACCEPTANCE


@pytest.mark.parametrize("radius,pressure", [
    (6000.0e3, 1.0e5),  # Earth sized
    (12.0e3, 1.0e5),
    (12.0e3, 5.0e4),
    (1000., 5.0e4),
    (0., 5.0e4),  # no inner volume
])
def test_thickness_from_radius_and_pressure(radius, pressure):
    assert_acceptable(
        inflation.t_RP(radius, pressure),
        old_inflation.t_RP(radius, pressure, rho)
    )
