#!/usr/bin/env python3
"""Monte Carlo transmission estimate for repeating connected-chevron shielding."""

from __future__ import annotations

import argparse
import math
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Params:
    n_samples: int
    seed: int
    tau_flat: float
    L: float
    p: float
    t: float
    theta_deg: float
    model: str
    tau_reference: str
    enforce_no_miss: bool
    pitch_margin: float
    require_no_hit: bool
    solve_thickness_for_flat: bool
    solve_depth_for_flat: bool
    t_min: float
    t_max: float
    d_min: float
    d_max: float
    solve_iters: int
    describe_variables: bool


def parse_args() -> Params:
    parser = argparse.ArgumentParser(
        description=(
            "Estimate average transmission T for a flat wall and for repeating "
            "connected-chevron shielding."
        )
    )
    parser.add_argument("--samples", type=int, default=200_000, help="Monte Carlo rays")
    parser.add_argument("--seed", type=int, default=7, help="RNG seed")
    parser.add_argument("--tau-flat", type=float, default=5.0, help="Reference tau for flat slab")
    parser.add_argument("--L", type=float, default=1.0, help="Chevron slab depth d in x")
    parser.add_argument("--pitch", type=float, default=0.5, help="Chevron periodic pitch p in z")
    parser.add_argument("--thickness", type=float, default=0.03, help="Blade attenuation thickness t")
    parser.add_argument("--theta-deg", type=float, default=45.0, help="Slat angle from x-axis")
    parser.add_argument(
        "--model",
        type=str,
        default="surface",
        choices=["surface", "strip"],
        help=(
            "surface: infinitesimally thin slat geometry, attenuation per crossing uses t/|n.u|; "
            "strip: finite geometric strip thickness in the x-z section"
        ),
    )
    parser.add_argument(
        "--tau-reference",
        type=str,
        default="blade",
        choices=["blade", "slab"],
        help=(
            "blade: tau_flat = lambda*t (normal blade hit); "
            "slab: tau_flat = lambda*L (flat slab depth)"
        ),
    )
    parser.add_argument(
        "--enforce-no-miss",
        action="store_true",
        help="Automatically reduce effective pitch (tiny amount) to satisfy conservative no-miss limit.",
    )
    parser.add_argument(
        "--pitch-margin",
        type=float,
        default=1e-6,
        help="Small subtraction from conservative pitch limit when --enforce-no-miss is used.",
    )
    parser.add_argument(
        "--require-no-hit",
        action="store_true",
        help="Exit nonzero if sampled no-hit rays are detected.",
    )
    parser.add_argument(
        "--solve-thickness-for-flat",
        action="store_true",
        help="Solve t such that T_chevron ~= T_flat_analytic.",
    )
    parser.add_argument(
        "--solve-depth-for-flat",
        action="store_true",
        help="Solve L (depth d) such that T_chevron ~= T_flat_analytic.",
    )
    parser.add_argument("--t-min", type=float, default=0.001, help="Lower bracket for thickness solve")
    parser.add_argument("--t-max", type=float, default=0.3, help="Upper bracket for thickness solve")
    parser.add_argument("--d-min", type=float, default=0.05, help="Lower bracket for depth solve")
    parser.add_argument("--d-max", type=float, default=5.0, help="Upper bracket for depth solve")
    parser.add_argument("--solve-iters", type=int, default=28, help="Bisection iterations")
    parser.add_argument(
        "--describe-variables",
        action="store_true",
        help="Print concise descriptions of all inputs and exit.",
    )

    args = parser.parse_args()

    if args.samples < 1:
        parser.error("--samples must be >= 1")
    if args.tau_flat <= 0:
        parser.error("--tau-flat must be > 0")
    if args.L <= 0:
        parser.error("--L must be > 0")
    if args.pitch <= 0:
        parser.error("--pitch must be > 0")
    if args.thickness <= 0:
        parser.error("--thickness must be > 0")
    if args.pitch_margin < 0:
        parser.error("--pitch-margin must be >= 0")
    if args.t_min <= 0 or args.t_max <= 0:
        parser.error("--t-min and --t-max must be > 0")
    if args.d_min <= 0 or args.d_max <= 0:
        parser.error("--d-min and --d-max must be > 0")
    if args.t_max <= args.t_min:
        parser.error("--t-max must be greater than --t-min")
    if args.d_max <= args.d_min:
        parser.error("--d-max must be greater than --d-min")
    if args.solve_iters < 1:
        parser.error("--solve-iters must be >= 1")
    if args.solve_depth_for_flat and args.solve_thickness_for_flat:
        parser.error("Choose at most one of --solve-depth-for-flat or --solve-thickness-for-flat")

    return Params(
        n_samples=args.samples,
        seed=args.seed,
        tau_flat=args.tau_flat,
        L=args.L,
        p=args.pitch,
        t=args.thickness,
        theta_deg=args.theta_deg,
        model=args.model,
        tau_reference=args.tau_reference,
        enforce_no_miss=args.enforce_no_miss,
        pitch_margin=args.pitch_margin,
        require_no_hit=args.require_no_hit,
        solve_thickness_for_flat=args.solve_thickness_for_flat,
        solve_depth_for_flat=args.solve_depth_for_flat,
        t_min=args.t_min,
        t_max=args.t_max,
        d_min=args.d_min,
        d_max=args.d_max,
        solve_iters=args.solve_iters,
        describe_variables=args.describe_variables,
    )


def describe_variables() -> None:
    print("Input Variables")
    print("samples: number of Monte Carlo rays")
    print("seed: RNG seed")
    print("tau_flat: flat-wall optical depth target (default 5)")
    print("L: chevron slab depth d in x direction")
    print("pitch: repeating period p in z direction")
    print("thickness: blade attenuation thickness t")
    print("theta_deg: slat angle from x-axis (45 means fixed 45-degree slats)")
    print("model: surface (zero geometric slat thickness) or strip (finite-width slats)")
    print("tau_reference: blade uses tau=lambda*t, slab uses tau=lambda*L")
    print("enforce_no_miss: tiny-adjust pitch downward to conservative no-miss limit")
    print("pitch_margin: tiny epsilon used by enforce_no_miss")
    print("require_no_hit: fail run if sampled P_no_hit > 0")
    print("solve_thickness_for_flat: solve t to match T_flat")
    print("solve_depth_for_flat: solve L (d) to match T_flat")
    print("t_min/t_max, d_min/d_max, solve_iters: solver bracket and bisection controls")


def sample_isotropic_hemisphere(rng: np.random.Generator, n: int) -> tuple[np.ndarray, np.ndarray]:
    """Return direction components (ux along +x, uz along z) for isotropic incoming flux."""
    u = rng.random(n)
    ux = np.sqrt(u)  # cosine-law weighting for incident flux on a plane
    phi = 2.0 * np.pi * rng.random(n)
    uz = np.sqrt(np.maximum(0.0, 1.0 - ux * ux)) * np.cos(phi)
    ux = np.maximum(ux, 1e-12)
    return ux, uz


def flat_transmission_analytic(tau: float, grid_n: int = 400_000) -> float:
    mu = np.linspace(1e-8, 1.0, grid_n)
    integrand = 2.0 * mu * np.exp(-tau / mu)
    return float(np.trapezoid(integrand, mu))


def lambda_from_params(params: Params, thickness: float, depth: float) -> float:
    if params.tau_reference == "blade":
        return params.tau_flat / thickness
    return params.tau_flat / depth


def conservative_pitch_limit(depth: float, thickness: float, theta_deg: float, model: str) -> float:
    theta = math.radians(theta_deg)
    base = 0.5 * depth * math.tan(theta)
    if model == "surface":
        return base
    c = max(math.cos(theta), 1e-15)
    return base + thickness / c


def effective_pitch(params: Params, depth: float, thickness: float) -> tuple[float, float]:
    p_lim = conservative_pitch_limit(depth, thickness, params.theta_deg, params.model)
    p_eff = params.p
    if params.enforce_no_miss:
        p_eff = min(params.p, max(1e-12, p_lim - params.pitch_margin))
    return p_eff, p_lim


def periodic_distance(value: float, period: float) -> float:
    wrapped = ((value + 0.5 * period) % period) - 0.5 * period
    return abs(wrapped)


def overlap_periodic_bands(lo: float, hi: float, p: float, w: float) -> float:
    if hi <= lo or w <= 0:
        return 0.0
    if w >= 0.5 * p:
        return hi - lo

    k_min = math.ceil((lo - w) / p)
    k_max = math.floor((hi + w) / p)
    total = 0.0
    for k in range(k_min, k_max + 1):
        c = k * p
        a = max(lo, c - w)
        b = min(hi, c + w)
        if b > a:
            total += b - a
    return total


def x_overlap_for_strip(a: float, b: float, x0: float, x1: float, p: float, w: float) -> float:
    if x1 <= x0 or w <= 0:
        return 0.0
    if w >= 0.5 * p:
        return x1 - x0

    if abs(a) < 1e-15:
        mid = b + a * (0.5 * (x0 + x1))
        return (x1 - x0) if periodic_distance(mid, p) <= w else 0.0

    y0 = a * x0 + b
    y1 = a * x1 + b
    lo = min(y0, y1)
    hi = max(y0, y1)
    y_overlap = overlap_periodic_bands(lo, hi, p, w)
    return y_overlap / abs(a)


def strip_material_length(ux: np.ndarray, uz: np.ndarray, z0: np.ndarray, depth: float, p: float, t: float, theta_deg: float) -> np.ndarray:
    theta = math.radians(theta_deg)
    m = math.tan(theta)
    w = (t / 2.0) / max(math.cos(theta), 1e-15)
    q = uz / ux
    x_mid = 0.5 * depth
    out = np.empty_like(ux)

    for i in range(ux.size):
        zi = float(z0[i])
        qi = float(q[i])

        a1 = qi - m
        b1 = zi
        lx1 = x_overlap_for_strip(a1, b1, 0.0, x_mid, p, w)

        a2 = qi + m
        b2 = zi - m * depth
        lx2 = x_overlap_for_strip(a2, b2, x_mid, depth, p, w)

        out[i] = (lx1 + lx2) / ux[i]
    return out


def count_integer_hits(y0: float, y1: float, p: float) -> int:
    lo = min(y0, y1)
    hi = max(y0, y1)
    k_min = math.ceil(lo / p)
    k_max = math.floor(hi / p)
    return max(0, int(k_max - k_min + 1))


def surface_material_length(ux: np.ndarray, uz: np.ndarray, z0: np.ndarray, depth: float, p: float, t: float, theta_deg: float) -> np.ndarray:
    theta = math.radians(theta_deg)
    m = math.tan(theta)
    q = uz / ux

    s = math.sin(theta)
    c = math.cos(theta)
    dot1 = np.abs(-s * ux + c * uz)
    dot2 = np.abs(+s * ux + c * uz)
    dot1 = np.maximum(dot1, 1e-12)
    dot2 = np.maximum(dot2, 1e-12)

    x_mid = 0.5 * depth
    out = np.empty_like(ux)

    for i in range(ux.size):
        zi = float(z0[i])
        qi = float(q[i])

        # Segment 1 centerlines: z = m*x + k*p for x in [0, L/2]
        y10 = zi
        y11 = zi + (qi - m) * x_mid
        n1 = count_integer_hits(y10, y11, p)

        # Segment 2 centerlines: z = m*L - m*x + k*p for x in [L/2, L]
        y20 = zi - m * depth + (qi + m) * x_mid
        y21 = zi - m * depth + (qi + m) * depth
        n2 = count_integer_hits(y20, y21, p)

        out[i] = n1 * (t / dot1[i]) + n2 * (t / dot2[i])

    return out


def material_length(
    params: Params, ux: np.ndarray, uz: np.ndarray, z0: np.ndarray, depth: float, pitch: float, thickness: float
) -> np.ndarray:
    if params.model == "surface":
        return surface_material_length(ux, uz, z0, depth, pitch, thickness, params.theta_deg)
    return strip_material_length(ux, uz, z0, depth, pitch, thickness, params.theta_deg)


def evaluate_case(
    params: Params, ux: np.ndarray, uz: np.ndarray, z0_unit: np.ndarray, depth: float, thickness: float
) -> tuple[float, float, float, float]:
    pitch_eff, pitch_lim = effective_pitch(params, depth, thickness)
    z0 = z0_unit * pitch_eff
    l_mat = material_length(params, ux, uz, z0, depth, pitch_eff, thickness)
    lam = lambda_from_params(params, thickness, depth)
    t_chev = float(np.mean(np.exp(-lam * l_mat)))
    p_no_hit = float(np.mean(l_mat <= 0.0))
    return t_chev, p_no_hit, pitch_eff, pitch_lim


def bisect_root(
    lo: float,
    hi: float,
    fn,
    target: float,
    iters: int,
) -> tuple[float, float, float, float, float]:
    t_lo, miss_lo, p_lo, lim_lo = fn(lo)
    t_hi, miss_hi, p_hi, lim_hi = fn(hi)
    f_lo = t_lo - target
    f_hi = t_hi - target

    if f_lo == 0.0:
        return lo, t_lo, miss_lo, p_lo, lim_lo
    if f_hi == 0.0:
        return hi, t_hi, miss_hi, p_hi, lim_hi
    if f_lo * f_hi > 0:
        raise SystemExit("No sign change in solver bracket.")

    mid = 0.5 * (lo + hi)
    t_mid = t_lo
    miss_mid = miss_lo
    p_mid = p_lo
    lim_mid = lim_lo
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        t_mid, miss_mid, p_mid, lim_mid = fn(mid)
        f_mid = t_mid - target
        if f_mid == 0.0:
            break
        if f_lo * f_mid <= 0:
            hi = mid
            f_hi = f_mid
        else:
            lo = mid
            f_lo = f_mid
    return mid, t_mid, miss_mid, p_mid, lim_mid


def main() -> None:
    params = parse_args()
    if params.describe_variables:
        describe_variables()
        return

    rng = np.random.default_rng(params.seed)
    ux, uz = sample_isotropic_hemisphere(rng, params.n_samples)
    z0_unit = rng.random(params.n_samples)

    t_flat_an = flat_transmission_analytic(params.tau_flat)
    t_flat_mc = float(np.mean(np.exp(-params.tau_flat / ux)))

    report_L = params.L
    report_t = params.t

    if params.solve_thickness_for_flat:
        fn = lambda th: evaluate_case(params, ux, uz, z0_unit, params.L, th)
        report_t, t_chev_mc, p_no_hit, p_eff, p_lim = bisect_root(
            params.t_min, params.t_max, fn, t_flat_an, params.solve_iters
        )
    elif params.solve_depth_for_flat:
        fn = lambda depth: evaluate_case(params, ux, uz, z0_unit, depth, params.t)
        report_L, t_chev_mc, p_no_hit, p_eff, p_lim = bisect_root(
            params.d_min, params.d_max, fn, t_flat_an, params.solve_iters
        )
    else:
        t_chev_mc, p_no_hit, p_eff, p_lim = evaluate_case(params, ux, uz, z0_unit, params.L, params.t)

    lam = lambda_from_params(params, report_t, report_L)
    tol = 1e-12 * max(1.0, abs(p_lim))
    pitch_ok = p_eff <= p_lim + tol

    print("Connected Chevron Monte Carlo")
    print(f"samples={params.n_samples} seed={params.seed}")
    print(
        f"geometry: model={params.model}, L={report_L:.6g}, p_input={params.p:.6g}, p_effective={p_eff:.6g}, "
        f"t={report_t:.6g}, theta={params.theta_deg:.6g} deg"
    )
    if params.solve_thickness_for_flat:
        print(f"thickness_solve_bracket=[{params.t_min:.6g}, {params.t_max:.6g}] iters={params.solve_iters}")
    if params.solve_depth_for_flat:
        print(f"depth_solve_bracket=[{params.d_min:.6g}, {params.d_max:.6g}] iters={params.solve_iters}")
    print(f"enforce_no_miss={params.enforce_no_miss}")
    print(f"pitch_no_miss_limit_conservative={p_lim:.10f}")
    print(f"pitch_satisfies_limit={pitch_ok}")
    print(f"tau_flat={params.tau_flat:.6g}")
    print(f"tau_reference={params.tau_reference}")
    print(f"lambda={lam:.6g}")
    print(f"T_flat_analytic={t_flat_an:.10f}")
    print(f"T_flat_MC={t_flat_mc:.10f}")
    print(f"P_no_hit={p_no_hit:.10f}")
    print(f"T_chevron_MC={t_chev_mc:.10f}")
    print(f"delta_T_chevron_minus_flat={t_chev_mc - t_flat_an:.10f}")

    if params.require_no_hit and p_no_hit > 0.0:
        raise SystemExit("No-hit rays detected while --require-no-hit was requested.")


if __name__ == "__main__":
    main()
