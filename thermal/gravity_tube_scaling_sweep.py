"""
Scaling sweep for rotating gravity tubes in a macro-atmosphere.

Outputs for a radius sweep:
- throat radius / area from 1g + 6 m/s tangential throat rule
- CO2 delta-ppm and indoor ppm for:
    (a) fixed 6 m/s axial throat draft
    (b) natural circulation air speed
- ideal natural-circulation "free jet" velocity for air and water
- required water flow to remove sensible heat
- equivalent single-pipe diameter if the water loop runs at the ideal natural-circulation water speed
- total water-pipe area / throat area ratio, using supply + return and the ideal natural-circulation water speed
  (ratio > 1 means even filling the whole throat with pipe cross-section would not suffice)

Assumptions are easy to edit below.
"""

from dataclasses import dataclass
import math
import pandas as pd


@dataclass
class Assumptions:
    g: float = 9.81
    v_throat_tangential: float = 6.0        # m/s
    axial_draft_fixed: float = 6.0          # m/s
    L_over_R: float = 2.0
    qpp: float = 20.0                       # W/m^2 average heat load on inner cylindrical area
    air_deltaT_K: float = 5.0 * 5.0 / 9.0  # 5 F
    water_deltaT_K: float = 20.0
    air_temp_K: float = 295.0
    beta_water: float = 2.1e-4             # 1/K
    rho_water: float = 1000.0              # kg/m^3
    cp_water: float = 4180.0               # J/kg/K
    area_per_person: float = 50.0          # m^2/person
    co2_gen_m3_s_per_person: float = 5.0e-6
    ambient_co2_ppm: float = 420.0
    water_area_fraction_of_throat: float = 0.25


def throat_radius(R: float, a: Assumptions) -> float:
    return a.v_throat_tangential * math.sqrt(R / a.g)


def throat_area(R: float, a: Assumptions) -> float:
    rt = throat_radius(R, a)
    return math.pi * rt * rt


def floor_area(R: float, a: Assumptions) -> float:
    L = a.L_over_R * R
    return 2.0 * math.pi * R * L


def total_heat(R: float, a: Assumptions) -> float:
    return floor_area(R, a) * a.qpp


def beta_air(a: Assumptions) -> float:
    return 1.0 / a.air_temp_K


def nat_circ_velocity_air(R: float, a: Assumptions) -> float:
    rt = throat_radius(R, a)
    omega2 = a.g / R
    return math.sqrt(beta_air(a) * a.air_deltaT_K * omega2 * (R*R - rt*rt))


def nat_circ_velocity_water(R: float, a: Assumptions) -> float:
    rt = throat_radius(R, a)
    omega2 = a.g / R
    return math.sqrt(a.beta_water * a.water_deltaT_K * omega2 * (R*R - rt*rt))


def people_count(R: float, a: Assumptions) -> float:
    return floor_area(R, a) / a.area_per_person


def co2_generation_total(R: float, a: Assumptions) -> float:
    return people_count(R, a) * a.co2_gen_m3_s_per_person


def co2_delta_ppm(R: float, airflow_m3_s: float, a: Assumptions) -> float:
    if airflow_m3_s <= 0:
        return float("inf")
    dx = co2_generation_total(R, a) / airflow_m3_s
    return dx * 1.0e6


def airflow_air(R: float, v_axial: float, a: Assumptions) -> float:
    return v_axial * throat_area(R, a)


def water_volume_flow_required(R: float, a: Assumptions) -> float:
    Q = total_heat(R, a)
    return Q / (a.rho_water * a.cp_water * a.water_deltaT_K)


def required_total_water_pipe_area(R: float, a: Assumptions) -> float:
    """
    Total required cross-sectional area for supply + return if each line runs at
    the ideal natural-circulation water speed.
    """
    v = nat_circ_velocity_water(R, a)
    if v <= 0:
        return float("inf")
    Vdot = water_volume_flow_required(R, a)
    return 2.0 * Vdot / v


def equivalent_single_pipe_diameter(R: float, a: Assumptions) -> float:
    """
    Equivalent diameter for one supply pipe carrying the full one-way flow
    at the ideal natural-circulation water speed.
    """
    v = nat_circ_velocity_water(R, a)
    if v <= 0:
        return float("inf")
    Vdot = water_volume_flow_required(R, a)
    area = Vdot / v
    return math.sqrt(4.0 * area / math.pi)


def water_pipe_area_ratio_to_throat(R: float, a: Assumptions) -> float:
    return required_total_water_pipe_area(R, a) / throat_area(R, a)


def available_water_area_ratio(R: float, a: Assumptions) -> float:
    """Ratio of required total pipe area to the allowed 1/4-throat utility zone."""
    return required_total_water_pipe_area(R, a) / (a.water_area_fraction_of_throat * throat_area(R, a))


def make_rows():
    a = Assumptions()
    rows = []
    R = 50.0
    while R <= 50000.0:
        At = throat_area(R, a)
        v_air_nat = nat_circ_velocity_air(R, a)
        v_w_nat = nat_circ_velocity_water(R, a)
        airflow_fixed = airflow_air(R, a.axial_draft_fixed, a)
        airflow_nat = airflow_air(R, v_air_nat, a)
        rows.append({
            "R_m": R,
            "L_m": a.L_over_R * R,
            "throat_radius_m": throat_radius(R, a),
            "throat_area_m2": At,
            "people_est": people_count(R, a),
            "air_nat_v_m_per_s": v_air_nat,
            "water_nat_v_m_per_s": v_w_nat,
            "co2_delta_ppm_fixed_6mps": co2_delta_ppm(R, airflow_fixed, a),
            "co2_indoor_ppm_fixed_6mps": a.ambient_co2_ppm + co2_delta_ppm(R, airflow_fixed, a),
            "co2_delta_ppm_natcirc": co2_delta_ppm(R, airflow_nat, a),
            "co2_indoor_ppm_natcirc": a.ambient_co2_ppm + co2_delta_ppm(R, airflow_nat, a),
            "heat_MW": total_heat(R, a) / 1e6,
            "water_flow_m3_per_s": water_volume_flow_required(R, a),
            "eq_single_supply_pipe_ID_m_at_vnat": equivalent_single_pipe_diameter(R, a),
            "total_pipe_area_to_throat_area_ratio": water_pipe_area_ratio_to_throat(R, a),
            "total_pipe_area_to_quarter_throat_ratio": available_water_area_ratio(R, a),
            "quarter_throat_nonviable": available_water_area_ratio(R, a) > 1.0,
        })
        R *= 1.5
    return pd.DataFrame(rows)


def main():
    df = make_rows()
    print(df.to_string(index=False, float_format=lambda x: f"{x:,.5g}"))


if __name__ == "__main__":
    main()
