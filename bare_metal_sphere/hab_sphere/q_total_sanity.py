from __future__ import annotations

import argparse
import math
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from hab_sphere.physics import MATERIAL_PRESETS
from hab_sphere.solve import solve_qppp_max

MIN_VALID_R_KM = 0.1


def _eps_tag(epsilon: float) -> str:
    return str(epsilon).replace(".", "p")


def _parse_h_i(h_i_str: str) -> float:
    s = h_i_str.strip().lower()
    if s in {"inf", "+inf", "infinity", "+infinity"}:
        return math.inf
    return float(h_i_str)


def _radius_grid(R_min_km: float, R_max_km: float, N: int, scale: str) -> np.ndarray:
    if scale == "linear":
        return np.linspace(R_min_km * 1_000.0, R_max_km * 1_000.0, N)
    return np.geomspace(R_min_km * 1_000.0, R_max_km * 1_000.0, N)


def _find_peak_then_decline(y: np.ndarray) -> int | None:
    dy = np.diff(y)
    positive_seen = False
    for i, d in enumerate(dy):
        if d > 0:
            positive_seen = True
        if positive_seen and d < 0:
            return i
    return None


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sanity plot: total Q versus radius, including allowable Q from thermal limit."
    )
    parser.add_argument("--material", choices=sorted(MATERIAL_PRESETS.keys()), default="steel")
    parser.add_argument("--p", type=float, default=101325.0)
    parser.add_argument("--sigma_allow", type=float, default=None)
    parser.add_argument("--k", type=float, default=None)
    parser.add_argument("--epsilon", type=float, default=0.8)
    parser.add_argument("--T_space", type=float, default=3.0)
    parser.add_argument("--T_in_max", type=float, default=303.0)
    parser.add_argument("--h_i", type=str, default="inf")
    parser.add_argument(
        "--temp_constraint_target",
        choices=["inner_surface", "air"],
        default="inner_surface",
    )
    parser.add_argument("--q_expected", type=float, default=0.023)
    parser.add_argument("--R_min_km", type=float, default=10.0)
    parser.add_argument("--R_max_km", type=float, default=10000.0)
    parser.add_argument("--N", type=int, default=500)
    parser.add_argument("--R_scale", choices=["linear", "log"], default="log")
    parser.add_argument("--out_dir", type=Path, default=None)
    return parser.parse_args()


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
    k = mat.k if args.k is None else args.k
    h_i = _parse_h_i(args.h_i)
    out_dir = args.out_dir if args.out_dir is not None else Path(args.material)
    out_dir.mkdir(parents=True, exist_ok=True)

    R_m = _radius_grid(args.R_min_km, args.R_max_km, args.N, args.R_scale)
    R_km = R_m / 1000.0
    volume = (4.0 / 3.0) * math.pi * R_m**3

    qppp_max = np.array(
        [
            solve_qppp_max(
                R_m=float(r),
                T_in_max=args.T_in_max,
                target=args.temp_constraint_target,
                p=args.p,
                sigma_allow=sigma_allow,
                k=k,
                epsilon=args.epsilon,
                T_space=args.T_space,
                h_i=h_i,
            )
            for r in R_m
        ]
    )

    Q_expected = args.q_expected * volume
    Q_allowable = qppp_max * volume

    peak_idx = _find_peak_then_decline(Q_allowable)
    if peak_idx is None:
        print("Q_allowable does not peak then decline within scanned R range.")
    else:
        peak_R_m = float(R_m[peak_idx])
        peak_Q = float(Q_allowable[peak_idx])
        print(
            "Q_allowable peaks then declines within scanned range at "
            f"R ~= {peak_R_m:.3f} m ({peak_R_m / 1000.0:.6g} km), "
            f"Q ~= {peak_Q:.6g} W."
        )

    fig, ax = plt.subplots(figsize=(9, 5.2))
    ax.plot(R_km, Q_expected, label=f"Q_expected (q'''={args.q_expected:g} W/m^3)")
    ax.plot(R_km, Q_allowable, label="Q_allowable from thermal limit")
    if peak_idx is not None:
        ax.scatter([R_km[peak_idx]], [Q_allowable[peak_idx]], marker="o", label="detected peak")
    ax.set_xscale(args.R_scale)
    ax.set_yscale("log")
    ax.set_xlabel("R (km)")
    ax.set_ylabel("Total heat Q (W)")
    ax.set_title(f"Total Q vs R ({args.material}, eps={args.epsilon:g})")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 0.02), framealpha=0.9)
    fig.tight_layout()

    out_path = out_dir / f"q_total_sanity_{args.material}_eps{_eps_tag(args.epsilon)}.png"
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
