from __future__ import annotations

from dataclasses import dataclass
import math


SIGMA_SB = 5.670374419e-8


@dataclass(frozen=True)
class Material:
    name: str
    k: float
    rho: float
    sigma_allow: float


MATERIAL_PRESETS = {
    "steel": Material(name="steel", k=50.0, rho=7850.0, sigma_allow=125e6),
    "al6061": Material(name="al6061", k=170.0, rho=2700.0, sigma_allow=138e6),
}


def pressure_thickness(R_m: float, p: float, sigma_allow: float) -> float:
    return p * R_m / (2.0 * sigma_allow)


def wall_areal_mass(R_m: float, p: float, sigma_allow: float, rho: float) -> float:
    return rho * pressure_thickness(R_m=R_m, p=p, sigma_allow=sigma_allow)


def q_flux(R_m: float, qppp: float) -> float:
    return qppp * R_m / 3.0


def t_out_from_flux(q_flux_w_m2: float, epsilon: float, T_space: float) -> float:
    return ((q_flux_w_m2 / (epsilon * SIGMA_SB)) + T_space**4) ** 0.25


def temperatures(
    *,
    R_m: float,
    qppp: float,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
) -> tuple[float, float, float]:
    t_p = pressure_thickness(R_m=R_m, p=p, sigma_allow=sigma_allow)
    qf = q_flux(R_m=R_m, qppp=qppp)
    T_out = t_out_from_flux(q_flux_w_m2=qf, epsilon=epsilon, T_space=T_space)
    dT_cond = qf * t_p / k
    dT_conv = 0.0 if math.isinf(h_i) else (qf / h_i)
    T_in_surf = T_out + dT_cond
    T_air = T_in_surf - dT_conv
    return T_in_surf, T_air, T_out


def shielding_radius_threshold(mu_req: float, sigma_allow: float, rho: float, p: float) -> float:
    return (2.0 * sigma_allow * mu_req) / (rho * p)

