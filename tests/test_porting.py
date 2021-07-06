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


@pytest.mark.parametrize("radius,mass", [
    (1.0e6, 1.0e15),
    (1.0e4, 1.0e13),
    (1000., 1.0e12),
    (0., 1.0e10),  # no inner volume
])
def test_pressure_from_radius_and_mass(radius, mass):
    assert_acceptable(
        inflation.P_RM(radius, mass),
        old_inflation.P_RM(radius, mass, rho)
    )
