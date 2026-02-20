from __future__ import annotations

import argparse
import csv
from pathlib import Path
import math

import numpy as np

from hab_sphere.physics import (
    MATERIAL_PRESETS,
    pressure_thickness,
    shielding_radius_threshold,
    wall_areal_mass,
)
from hab_sphere.solve import solve_qppp_max
from hab_sphere.plots import plot_combined, plot_shielding, plot_thermal

MIN_VALID_R_KM = 0.1


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Spherical habitat feasibility plots.")
    parser.add_argument("--material", choices=sorted(MATERIAL_PRESETS.keys()), default="steel")

    parser.add_argument("--p", type=float, default=101325.0)
    parser.add_argument("--sigma_allow", type=float, default=None)
    parser.add_argument("--rho", type=float, default=None)
    parser.add_argument("--k", type=float, default=None)
    parser.add_argument("--epsilon", type=float, default=0.2)
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
    parser.add_argument("--N", type=int, default=400)
    parser.add_argument("--R_scale", choices=["linear", "log"], default="log")
    parser.add_argument("--out_dir", type=Path, default=None)

    return parser.parse_args()


def _epsilon_values(args: argparse.Namespace) -> list[float]:
    if args.epsilon_list:
        eps_vals = []
        for part in args.epsilon_list.split(","):
            part = part.strip()
            if not part:
                continue
            eps_vals.append(float(part))
        if not eps_vals:
            raise ValueError("epsilon_list provided but no values parsed")
        return eps_vals
    return [args.epsilon]


def _parse_h_i(h_i_str: str) -> float:
    s = h_i_str.strip().lower()
    if s in {"inf", "+inf", "infinity", "+infinity"}:
        return math.inf
    return float(h_i_str)


def _radius_grid(R_min_km: float, R_max_km: float, N: int, scale: str) -> np.ndarray:
    if scale == "linear":
        return np.linspace(R_min_km * 1_000.0, R_max_km * 1_000.0, N)
    return np.geomspace(R_min_km * 1_000.0, R_max_km * 1_000.0, N)


def _first_radius_km_where(mask: np.ndarray, R_km: np.ndarray) -> float | None:
    idx = np.where(mask)[0]
    if len(idx) == 0:
        return None
    return float(R_km[idx[0]])


def main() -> None:
    args = _parse_args()
    if args.R_min_km < MIN_VALID_R_KM:
        raise ValueError(
            f"R_min_km must be >= {MIN_VALID_R_KM} km (100 m) for model validity; got {args.R_min_km}"
        )
    if args.R_max_km <= args.R_min_km:
        raise ValueError(f"R_max_km must be greater than R_min_km; got {args.R_max_km} <= {args.R_min_km}")

    mat = MATERIAL_PRESETS[args.material]
    sigma_allow = mat.sigma_allow if args.sigma_allow is None else args.sigma_allow
    rho = mat.rho if args.rho is None else args.rho
    k = mat.k if args.k is None else args.k
    h_i = _parse_h_i(args.h_i)
    epsilon_values = _epsilon_values(args)

    out_dir = args.out_dir if args.out_dir is not None else Path(args.material)
    out_dir.mkdir(parents=True, exist_ok=True)
    R_m = _radius_grid(args.R_min_km, args.R_max_km, args.N, args.R_scale)
    R_km = R_m / 1_000.0

    t_m = np.array([pressure_thickness(r, args.p, sigma_allow) for r in R_m])
    mu_wall = np.array([wall_areal_mass(r, args.p, sigma_allow, rho) for r in R_m])
    ok_shielding = mu_wall >= args.mu_req

    shielding_plot_path = plot_shielding(
        out_dir=out_dir,
        material=args.material,
        R_km=R_km,
        mu_wall=mu_wall,
        mu_req=args.mu_req,
        xscale=args.R_scale,
    )
    print(f"Wrote {shielding_plot_path}")

    report_sections: list[dict[str, str | float]] = []

    for epsilon in epsilon_values:
        qppp_max = np.array(
            [
                solve_qppp_max(
                    R_m=float(r),
                    T_in_max=args.T_in_max,
                    target=args.temp_constraint_target,
                    p=args.p,
                    sigma_allow=sigma_allow,
                    k=k,
                    epsilon=epsilon,
                    T_space=args.T_space,
                    h_i=h_i,
                )
                for r in R_m
            ]
        )

        ok_thermal = qppp_max >= args.q_expected
        ok_both = ok_thermal & ok_shielding

        thermal_plot_path = plot_thermal(
            out_dir=out_dir,
            material=args.material,
            epsilon=epsilon,
            R_km=R_km,
            qppp_max=qppp_max,
            q_expected=args.q_expected,
            xscale=args.R_scale,
        )
        combined_plot_path = plot_combined(
            out_dir=out_dir,
            material=args.material,
            epsilon=epsilon,
            R_km=R_km,
            qppp_max=qppp_max,
            q_expected=args.q_expected,
            mu_wall=mu_wall,
            mu_req=args.mu_req,
            xscale=args.R_scale,
        )
        print(f"Wrote {thermal_plot_path}")
        print(f"Wrote {combined_plot_path}")

        eps_tag = str(epsilon).replace(".", "p")
        csv_path = out_dir / f"results_{args.material}_eps{eps_tag}.csv"
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "R_m",
                    "R_km",
                    "t_m",
                    "mu_wall",
                    "qppp_max",
                    "ok_thermal",
                    "ok_shielding",
                    "ok_both",
                ]
            )
            for i in range(len(R_m)):
                writer.writerow(
                    [
                        float(R_m[i]),
                        float(R_km[i]),
                        float(t_m[i]),
                        float(mu_wall[i]),
                        float(qppp_max[i]),
                        int(ok_thermal[i]),
                        int(ok_shielding[i]),
                        int(ok_both[i]),
                    ]
                )
        print(f"Wrote {csv_path}")

        r_thermal = _first_radius_km_where(ok_thermal, R_km)
        r_shield = _first_radius_km_where(ok_shielding, R_km)
        r_both = _first_radius_km_where(ok_both, R_km)
        r_shield_analytic_km = (
            shielding_radius_threshold(
                mu_req=args.mu_req,
                sigma_allow=sigma_allow,
                rho=rho,
                p=args.p,
            )
            / 1000.0
        )

        print("")
        print(
            "Summary: "
            f"material={args.material}, epsilon={epsilon:g}, "
            f"target={args.temp_constraint_target}, T_in_max={args.T_in_max:g} K, "
            f"q_expected={args.q_expected:g} W/m^3, mu_req={args.mu_req:g} kg/m^2"
        )
        print(f"  First R where thermal passes (km): {r_thermal if r_thermal is not None else 'none'}")
        print(f"  First R where shielding passes (km): {r_shield if r_shield is not None else 'none'}")
        print(f"  First R where both pass (km): {r_both if r_both is not None else 'none'}")
        print(f"  Analytic shielding threshold R_shield (km): {r_shield_analytic_km:.6g}")

        report_sections.append(
            {
                "epsilon": epsilon,
                "thermal_plot": thermal_plot_path.name,
                "combined_plot": combined_plot_path.name,
                "csv": csv_path.name,
                "r_thermal": "none" if r_thermal is None else f"{r_thermal:.6g}",
                "r_shield": "none" if r_shield is None else f"{r_shield:.6g}",
                "r_both": "none" if r_both is None else f"{r_both:.6g}",
            }
        )

    report_path = out_dir / "README.md"
    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Habitat Sphere Output Report\n\n")
        f.write("[Back to parent README](../README.md)\n\n")
        f.write("Generated by `python -m hab_sphere.cli`.\n\n")
        f.write("## Run Parameters\n\n")
        f.write(f"- material: `{args.material}`\n")
        f.write(f"- p (Pa): `{args.p}`\n")
        f.write(f"- sigma_allow (Pa): `{sigma_allow}`\n")
        f.write(f"- rho (kg/m^3): `{rho}`\n")
        f.write(f"- k (W/m/K): `{k}`\n")
        f.write(f"- T_space (K): `{args.T_space}`\n")
        f.write(f"- T_in_max (K): `{args.T_in_max}`\n")
        f.write(f"- h_i (W/m^2/K): `{'inf' if math.isinf(h_i) else h_i}`\n")
        f.write(f"- temp_constraint_target: `{args.temp_constraint_target}`\n")
        f.write(f"- q_expected (W/m^3): `{args.q_expected}`\n")
        f.write(f"- mu_req (kg/m^2): `{args.mu_req}`\n")
        f.write(f"- radius range (km): `{args.R_min_km}` to `{args.R_max_km}`\n")
        f.write(f"- N: `{args.N}`\n")
        f.write(f"- R_scale: `{args.R_scale}`\n")
        f.write("\n")
        f.write("## Shielding Plot\n\n")
        f.write(f"![shielding]({shielding_plot_path.name})\n\n")
        for sec in report_sections:
            f.write(f"## Epsilon {sec['epsilon']:g}\n\n")
            f.write(f"- first thermal-pass radius (km): `{sec['r_thermal']}`\n")
            f.write(f"- first shielding-pass radius (km): `{sec['r_shield']}`\n")
            f.write(f"- first both-pass radius (km): `{sec['r_both']}`\n")
            f.write(f"- csv: `{sec['csv']}`\n\n")
            f.write(f"![thermal eps {sec['epsilon']:g}]({sec['thermal_plot']})\n\n")
            f.write(f"![combined eps {sec['epsilon']:g}]({sec['combined_plot']})\n\n")

    print(f"Wrote {report_path}")


if __name__ == "__main__":
    main()
