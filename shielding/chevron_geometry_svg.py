#!/usr/bin/env python3
"""Render chevron geometry + sample rays to SVG, with per-ray evaluated material thickness/path."""

from __future__ import annotations

import argparse
import math

import numpy as np

import monte_carlo_chevron as mc


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Draw connected chevron geometry and labeled sample rays.")
    p.add_argument("--L", type=float, default=1.0, help="Depth d in x")
    p.add_argument("--pitch", type=float, default=0.5, help="Input pitch p in z")
    p.add_argument("--thickness", type=float, default=0.03, help="Blade attenuation thickness t")
    p.add_argument("--theta-deg", type=float, default=45.0, help="Slat angle")
    p.add_argument("--model", type=str, default="surface", choices=["surface", "surface_extended", "strip"])
    p.add_argument(
        "--center-extension-frac",
        type=float,
        default=0.0,
        help="For model=surface_extended: asymmetric '/'-branch extension fraction of L toward +x.",
    )
    p.add_argument("--tau-flat", type=float, default=5.0)
    p.add_argument("--tau-reference", type=str, default="blade", choices=["blade", "slab"])
    p.add_argument("--num-rays", type=int, default=14, help="How many dotted rays to show")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--periods", type=int, default=3, help="How many z periods to draw")
    p.add_argument("--enforce-no-miss", action="store_true")
    p.add_argument("--pitch-margin", type=float, default=1e-6)
    p.add_argument("--out", type=str, default="chevron_geometry.svg")
    return p.parse_args()


def sx(x: float, width: float, margin: float, L: float) -> float:
    return margin + (x / L) * width


def sz(z: float, height: float, margin: float, zmin: float, zmax: float) -> float:
    # SVG y-axis points downward.
    return margin + (1.0 - (z - zmin) / (zmax - zmin)) * height


def line(x1: float, y1: float, x2: float, y2: float, style: str) -> str:
    return f'<line x1="{x1:.3f}" y1="{y1:.3f}" x2="{x2:.3f}" y2="{y2:.3f}" style="{style}" />'


def text(x: float, y: float, s: str, style: str) -> str:
    return f'<text x="{x:.3f}" y="{y:.3f}" style="{style}">{s}</text>'


def main() -> None:
    a = parse_args()

    params = mc.Params(
        n_samples=1,
        seed=a.seed,
        tau_flat=a.tau_flat,
        L=a.L,
        p=a.pitch,
        t=a.thickness,
        theta_deg=a.theta_deg,
        model=a.model,
        tau_reference=a.tau_reference,
        enforce_no_miss=a.enforce_no_miss,
        pitch_margin=a.pitch_margin,
        require_no_hit=False,
        solve_thickness_for_flat=False,
        solve_depth_for_flat=False,
        t_min=0.001,
        t_max=0.3,
        d_min=0.05,
        d_max=5.0,
        solve_iters=28,
        describe_variables=False,
        center_extension_frac=a.center_extension_frac,
    )

    p_eff, p_lim = mc.effective_pitch(params, a.L, a.thickness)

    margin = 40.0
    W = 980.0
    H = 680.0
    inner_w = W - 2 * margin
    inner_h = H - 2 * margin

    zmin = -0.25 * p_eff
    zmax = (a.periods + 0.25) * p_eff
    zspan = zmax - zmin

    ext = a.center_extension_frac * a.L if a.model == "surface_extended" else 0.0
    x_min = -ext if a.model == "surface_extended" else 0.0
    x_span = a.L - x_min

    # Keep x/z plot units isotropic so geometric angles render correctly.
    scale = min(inner_w / x_span, inner_h / zspan)
    draw_w = x_span * scale
    draw_h = zspan * scale
    x_pad = margin + 0.5 * (inner_w - draw_w)
    y_pad = margin + 0.5 * (inner_h - draw_h)

    def sx_plot(x: float) -> float:
        return x_pad + ((x - x_min) / x_span) * draw_w

    def sz_plot(z: float) -> float:
        return sz(z, draw_h, y_pad, zmin, zmax)

    theta = math.radians(a.theta_deg)
    m = math.tan(theta)

    parts = []
    parts.append('<?xml version="1.0" encoding="UTF-8"?>')
    parts.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    parts.append('<rect x="0" y="0" width="100%" height="100%" fill="#ffffff"/>')

    # Frame and axes.
    x0 = sx_plot(x_min)
    x_entry = sx_plot(0.0)
    xL = sx_plot(a.L)
    z0v = sz_plot(zmin)
    z1v = sz_plot(zmax)
    parts.append(line(x0, z0v, xL, z0v, "stroke:#444;stroke-width:1"))
    parts.append(line(x0, z1v, xL, z1v, "stroke:#444;stroke-width:1"))
    parts.append(line(x0, z0v, x0, z1v, "stroke:#444;stroke-width:1"))
    parts.append(line(x_entry, z0v, x_entry, z1v, "stroke:#888;stroke-width:1;stroke-dasharray:3,3"))
    parts.append(line(xL, z0v, xL, z1v, "stroke:#444;stroke-width:1"))

    # Period guides.
    for k in range(a.periods + 1):
        zk = k * p_eff
        yk = sz_plot(zk)
        parts.append(line(x0, yk, xL, yk, "stroke:#ddd;stroke-width:1"))
        parts.append(text(xL + 6, yk + 4, f"z={zk:.4f}", "font:12px monospace;fill:#666"))

    # Chevron centerlines.
    style_chev = "stroke:#d11;stroke-width:2;fill:none"
    x1_lo, x1_hi = (-ext, 0.5 * a.L) if a.model == "surface_extended" else (0.0, 0.5 * a.L)
    x2_lo, x2_hi = 0.5 * a.L, a.L
    for k in range(-1, a.periods + 2):
        zoff = k * p_eff
        z1a = zoff + m * x1_lo
        z1b = zoff + m * x1_hi
        z2a = zoff + m * a.L - m * x2_lo
        z2b = zoff + m * a.L - m * x2_hi
        parts.append(line(sx_plot(x1_lo), sz_plot(z1a), sx_plot(x1_hi), sz_plot(z1b), style_chev))
        parts.append(line(sx_plot(x2_lo), sz_plot(z2a), sx_plot(x2_hi), sz_plot(z2b), style_chev))

    # Sample rays.
    rng = np.random.default_rng(a.seed)
    ux, uz = mc.sample_isotropic_hemisphere(rng, a.num_rays)
    z0_unit = rng.random(a.num_rays)

    for i in range(a.num_rays):
        zstart = float(z0_unit[i] * p_eff + (i % a.periods) * p_eff)
        q = float(uz[i] / ux[i])
        x_ray_start = x_min
        x_ray_end = a.L
        zend = zstart + q * (x_ray_end - x_ray_start)
        z_at_x0 = zstart - q * x_ray_start

        # Evaluate material length for this specific ray.
        li = mc.material_length(
            params,
            np.array([ux[i]]),
            np.array([uz[i]]),
            np.array([z_at_x0]),
            a.L,
            p_eff,
            a.thickness,
        )[0]
        hi = mc.hit_count_distribution(
            params,
            np.array([ux[i]]),
            np.array([uz[i]]),
            np.array([z_at_x0]),
            a.L,
            p_eff,
        )
        htxt = int(hi[0]) if hi is not None else -1

        x1 = sx_plot(x_ray_start)
        y1 = sz_plot(zstart)
        x2 = sx_plot(x_ray_end)
        y2 = sz_plot(zend)
        parts.append(line(x1, y1, x2, y2, "stroke:#0a58ca;stroke-width:1.4;stroke-dasharray:4,4"))

        xm = 0.55 * x1 + 0.45 * x2
        ym = 0.55 * y1 + 0.45 * y2 - 4
        label = f"h={htxt}, Lmat={li:.4f}" if htxt >= 0 else f"Lmat={li:.4f}"
        parts.append(text(xm, ym, label, "font:11px monospace;fill:#0a58ca"))

    # Header labels.
    parts.append(text(margin, 20, "Connected Chevron Geometry", "font:16px monospace;font-weight:bold;fill:#111"))
    parts.append(
        text(
            margin,
            36,
            f"model={a.model}, L={a.L:.6g}, p_input={a.pitch:.6g}, p_effective={p_eff:.6g}, t={a.thickness:.6g}, theta={a.theta_deg:.6g}",
            "font:12px monospace;fill:#333",
        )
    )
    parts.append(
        text(
            margin,
            52,
            f"pitch_no_miss_limit_conservative={p_lim:.10f}, enforce_no_miss={a.enforce_no_miss}, ext_frac={a.center_extension_frac:.4g}",
            "font:12px monospace;fill:#333",
        )
    )
    if a.model == "surface_extended":
        parts.append(
            text(
                margin,
                68,
                "Dashed vertical line marks x=0 entry plane; frame includes left extension region.",
                "font:12px monospace;fill:#333",
            )
        )

    parts.append("</svg>")

    with open(a.out, "w", encoding="utf-8") as f:
        f.write("\n".join(parts) + "\n")

    print(f"Wrote {a.out}")
    print(f"p_effective={p_eff:.10f}")
    print(f"pitch_no_miss_limit_conservative={p_lim:.10f}")


if __name__ == "__main__":
    main()
