import pytest

from math import pi

from gb import inflation
from gb.ported import gravity as old_inflation

from gb.constants import rho


ACCEPTANCE = 1.0e-9


CASES = [
    # case name     M           P                R
    ["sun_small", 1.989e30, 120704368942104.95, 0.0],
    ["sun_medium", 1.989e30, 21099377645395.375, 714826987.5913494],
    ["sun_large", 1.989e30, 4019905665.58473, 7148269875.913494],
    ["earth_small", 5.972e27, 2512154432696.3853, 0.0],
    ["earth_medium", 5.972e27, 439129880248.4786, 103124679.65671049],
    ["earth_large", 5.972e27, 83664111.95654, 1031246796.5671049],
    ["moon_small", 7.346e25, 133865012771.37538, 0.0],
    ["moon_medium", 7.346e25, 23399885875.908424, 23805263.194816392],
    ["moon_large", 7.346e25, 4458204.1891207425, 238052631.94816393],
    ["ceres_small", 9.38e23, 7313103052.868566, 0.0],
    ["ceres_medium", 9.38e23, 1278345799.9451523, 5564040.624867016],
    ["ceres_large", 9.38e23, 243553.60665793912, 55640406.24867016],
    ["vesta_small", 2.59e20, 31009848.45253202, 0.0],
    ["vesta_medium", 2.59e20, 5420586.752251058, 362317.4636663841],
    ["vesta_large", 2.59e20, 1032.7436080043185, 3623174.636663841],
    ["hygiea_small", 8.3e19, 14521735.738147829, 0.0],
    ["hygiea_medium", 8.3e19, 2538429.959836274, 247941.20654198257],
    ["hygiea_large", 8.3e19, 483.6279604418672, 2479412.0654198257],
    ["psyche_small", 2.4e19, 6350003.464412078, 0.0],
    ["psyche_medium", 2.4e19, 1109993.965582771, 163955.6648803104],
    ["psyche_large", 2.4e19, 211.47879837977686, 1639556.648803104],
    ["phobos_small", 1.0659e16, 36963.870713292745, 0.0],
    ["phobos_medium", 1.0659e16, 6461.362370312837, 12509.16055914635],
    ["phobos_large", 1.0659e16, 1.2310347554481575, 125091.6055914635],
]


def assert_acceptable(new, old, ref=None):
    if ref is None:
        denom = old
    else:
        denom = ref
    assert abs(new - old) / denom < ACCEPTANCE


@pytest.mark.parametrize("mass,pressure,radius", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_thickness_from_radius_and_pressure(mass, pressure, radius):
    assert_acceptable(
        inflation.t_RP(radius, pressure), old_inflation.t_RP(radius, pressure, rho)
    )


@pytest.mark.parametrize("mass,pressure,radius", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_pressure_from_radius_and_mass(mass, pressure, radius):
    assert_acceptable(
        inflation.P_RM(radius, mass), old_inflation.P_RM(radius, mass, rho)
    )


@pytest.mark.parametrize("mass,pressure,radius", [c[1:] for c in CASES], ids=[c[0] for c in CASES])
def test_radius_from_mass_and_pressure(mass, pressure, radius):
    R0 = (mass * 3. / (4. * pi * rho))**(1./3.)
    assert_acceptable(
        inflation.R_MP(mass, pressure), radius, ref=R0
    )
    # old method was not fully correct, so no testing against old_inflation.R_MP
