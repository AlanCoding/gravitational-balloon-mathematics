from __future__ import annotations

import argparse
import math
from typing import Iterable

import numpy as np

from hab_sphere.physics import MATERIAL_PRESETS, shielding_radius_threshold, temperatures

MIN_VALID_R_KM = 0.1


def _parse_h_i(h_i_str: str) -> float:
    s = h_i_str.strip().lower()
    if s in {"inf", "+inf", "infinity", "+infinity"}:
        return math.inf
    return float(h_i_str)


def _epsilon_values(epsilon: float, epsilon_list: str | None) -> list[float]:
    if not epsilon_list:
        return [epsilon]
    vals: list[float] = []
    for part in epsilon_list.split(","):
        part = part.strip()
        if part:
            vals.append(float(part))
    if not vals:
        raise ValueError("epsilon_list provided but no values parsed")
    return vals


def _target_temp(
    *,
    target: str,
    R_m: float,
    qppp: float,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
) -> float:
    T_in_surf, T_air, _ = temperatures(
        R_m=R_m,
        qppp=qppp,
        p=p,
        sigma_allow=sigma_allow,
        k=k,
        epsilon=epsilon,
        T_space=T_space,
        h_i=h_i,
    )
    if target == "inner_surface":
        return T_in_surf
    if target == "air":
        return T_air
    raise ValueError(f"Unknown temp target: {target}")


def _thermal_g(
    R_m: float,
    *,
    q_expected: float,
    T_in_max: float,
    target: str,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
) -> float:
    return (
        _target_temp(
            target=target,
            R_m=R_m,
            qppp=q_expected,
            p=p,
            sigma_allow=sigma_allow,
            k=k,
            epsilon=epsilon,
            T_space=T_space,
            h_i=h_i,
        )
        - T_in_max
    )


def _bisect_root(
    left: float,
    right: float,
    fn,
    max_iter: int = 120,
    tol_abs: float = 1e-9,
) -> float:
    f_left = fn(left)
    f_right = fn(right)
    if f_left == 0.0:
        return left
    if f_right == 0.0:
        return right
    if f_left * f_right > 0.0:
        raise ValueError("Bisection interval does not bracket a root")

    lo, hi = left, right
    flo, fhi = f_left, f_right
    for _ in range(max_iter):
        mid = 0.5 * (lo + hi)
        fmid = fn(mid)
        if abs(fmid) <= tol_abs:
            return mid
        if flo * fmid <= 0.0:
            hi = mid
            fhi = fmid
        else:
            lo = mid
            flo = fmid
    return 0.5 * (lo + hi)


def _thermal_crossovers(
    *,
    R_m_grid: np.ndarray,
    q_expected: float,
    T_in_max: float,
    target: str,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
) -> tuple[float | None, float | None]:
    g_vals = np.array(
        [
            _thermal_g(
                float(r),
                q_expected=q_expected,
                T_in_max=T_in_max,
                target=target,
                p=p,
                sigma_allow=sigma_allow,
                k=k,
                epsilon=epsilon,
                T_space=T_space,
                h_i=h_i,
            )
            for r in R_m_grid
        ]
    )
    ok = g_vals <= 0.0
    idx_true = np.where(ok)[0]
    if len(idx_true) == 0:
        return None, None

    r_min = float(R_m_grid[idx_true[0]])
    r_max = float(R_m_grid[idx_true[-1]])

    def fn(r: float) -> float:
        return _thermal_g(
            r,
            q_expected=q_expected,
            T_in_max=T_in_max,
            target=target,
            p=p,
            sigma_allow=sigma_allow,
            k=k,
            epsilon=epsilon,
            T_space=T_space,
            h_i=h_i,
        )

    # Refine lower boundary if it transitions from fail->pass.
    i0 = idx_true[0]
    if i0 > 0 and g_vals[i0 - 1] * g_vals[i0] <= 0.0:
        r_min = _bisect_root(float(R_m_grid[i0 - 1]), float(R_m_grid[i0]), fn)

    # Refine upper boundary if it transitions from pass->fail.
    i1 = idx_true[-1]
    if i1 < len(R_m_grid) - 1 and g_vals[i1] * g_vals[i1 + 1] <= 0.0:
        r_max = _bisect_root(float(R_m_grid[i1]), float(R_m_grid[i1 + 1]), fn)

    return r_min, r_max


def _fmt_radius(r_m: float | None) -> str:
    if r_m is None:
        return "none"
    return f"{r_m:,.3f} m ({r_m / 1000.0:,.6g} km)"


def _fmt_interval(r_min: float | None, r_max: float | None) -> str:
    if r_min is None or r_max is None:
        return "none"
    return f"[{_fmt_radius(r_min)} .. {_fmt_radius(r_max)}]"


def _material_iter(material_filter: str | None) -> Iterable[tuple[str, object]]:
    if material_filter:
        mat = MATERIAL_PRESETS[material_filter]
        return [(material_filter, mat)]
    return [(k, v) for k, v in MATERIAL_PRESETS.items()]


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Numeric crossover summary (no plots) across materials."
    )
    parser.add_argument("--material", choices=sorted(MATERIAL_PRESETS.keys()), default=None)
    parser.add_argument("--p", type=float, default=101325.0)
    parser.add_argument("--epsilon", type=float, default=0.8)
    parser.add_argument("--epsilon_list", type=str, default=None)
    parser.add_argument("--T_space", type=float, default=3.0)
    parser.add_argument("--T_in_max", type=float, default=303.0)
    parser.add_argument("--h_i", type=str, default="inf")
    parser.add_argument(
        "--temp_constraint_target",
        choices=["inner_surface", "air"],
        default="inner_surface",
    )
    parser.add_argument("--q_expected", type=float, default=0.023)
    parser.add_argument("--mu_req", type=float, default=2000.0)
    parser.add_argument("--R_min_km", type=float, default=0.1)
    parser.add_argument("--R_max_km", type=float, default=200.0)
    parser.add_argument("--N", type=int, default=2000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    if args.R_min_km < MIN_VALID_R_KM:
        raise ValueError(
            f"R_min_km must be >= {MIN_VALID_R_KM} km (100 m) for model validity; got {args.R_min_km}"
        )
    if args.R_max_km <= args.R_min_km:
        raise ValueError(f"R_max_km must be greater than R_min_km; got {args.R_max_km} <= {args.R_min_km}")

    eps_values = _epsilon_values(args.epsilon, args.epsilon_list)
    h_i = _parse_h_i(args.h_i)
    R_m_grid = np.geomspace(args.R_min_km * 1000.0, args.R_max_km * 1000.0, args.N)

    print("Habitat Sphere Numeric Crossover Summary")
    print(f"q_expected = {args.q_expected} W/m^3, mu_req = {args.mu_req} kg/m^2")
    print(f"T_in_max = {args.T_in_max} K, target = {args.temp_constraint_target}, T_space = {args.T_space} K")
    print(f"h_i = {'inf' if math.isinf(h_i) else h_i} W/m^2/K")
    print(f"R search range = {args.R_min_km}..{args.R_max_km} km, N = {args.N}")
    print("")

    for material_name, mat in _material_iter(args.material):
        print(f"Material: {material_name}")
        print(f"  sigma_allow = {mat.sigma_allow:.6g} Pa, rho = {mat.rho:.6g} kg/m^3, k = {mat.k:.6g} W/m/K")
        for eps in eps_values:
            r_shield = shielding_radius_threshold(
                mu_req=args.mu_req,
                sigma_allow=mat.sigma_allow,
                rho=mat.rho,
                p=args.p,
            )
            r_thermal_min, r_thermal_max = _thermal_crossovers(
                R_m_grid=R_m_grid,
                q_expected=args.q_expected,
                T_in_max=args.T_in_max,
                target=args.temp_constraint_target,
                p=args.p,
                sigma_allow=mat.sigma_allow,
                k=mat.k,
                epsilon=eps,
                T_space=args.T_space,
                h_i=h_i,
            )

            combined_min = None
            combined_max = None
            if r_thermal_min is not None and r_thermal_max is not None:
                combined_min = max(r_shield, r_thermal_min)
                combined_max = r_thermal_max
                if combined_min > combined_max:
                    combined_min = None
                    combined_max = None

            print(f"  epsilon = {eps:g}")
            print(f"    shielding crossover (min R): {_fmt_radius(r_shield)}")
            print(
                "    thermal feasible interval at q_expected: "
                f"{_fmt_interval(r_thermal_min, r_thermal_max)}"
            )
            print(
                "    combined feasible interval (thermal & shielding): "
                f"{_fmt_interval(combined_min, combined_max)}"
            )
        print("")


if __name__ == "__main__":
    main()
