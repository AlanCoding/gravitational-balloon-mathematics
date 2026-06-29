#!/usr/bin/env python3
"""Render the first visualization pass as standalone SVG files."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ORDINARY_PLANETS = {"Mercury", "Venus", "Earth", "Mars"}
ORDINARY_MOONS = {"Earth", "Mars"}
ASTEROID_DETAIL_THRESHOLD_KG = 1e17
ASTEROID_DETAIL_THRESHOLD_AREA_KM2 = 1e5
STRIP_P_MAX = 2.95e6
EXCAVATION_RHO = 3000.0
BODY_COLOR_OVERRIDES = {
    "Mercury": "#b45309",
    "Venus": "#d97706",
    "Earth": "#2563eb",
    "Mars": "#dc2626",
    "Moon": "#6b7280",
    "Phobos": "#0f766e",
    "Deimos": "#14b8a6",
    "Ceres": "#7c3aed",
    "Vesta": "#8b5cf6",
    "Pallas": "#9333ea",
    "Hygiea": "#a855f7",
    "Interamnia": "#6366f1",
    "Psyche": "#c026d3",
    "Camilla": "#0ea5e9",
    "Kalliope": "#4f46e5",
    "Lutetia": "#1d4ed8",
}
PLANET_SHADES = ["#b45309", "#d97706", "#ea580c", "#2563eb"]
MOON_SHADES = ["#6b7280", "#0f766e", "#14b8a6"]
ASTEROID_SHADES = [
    "#7c3aed",
    "#8b5cf6",
    "#9333ea",
    "#a855f7",
    "#6366f1",
    "#c026d3",
    "#4f46e5",
    "#1d4ed8",
]


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def load_usability(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as f:
        return {row["body_id"]: row for row in csv.DictReader(f)}


def selected(row: dict[str, str]) -> bool:
    kind = row["kind"]
    if kind == "planet":
        return row["name"] in ORDINARY_PLANETS
    if kind == "moon":
        return row["parent"] in ORDINARY_MOONS
    if kind == "asteroid":
        return True
    return False


def mass(row: dict[str, str]) -> float:
    return float(row["reachable_mass_kg"])


def surface_area(row: dict[str, str]) -> float:
    radius_km = float(row["radius_km"])
    return 4.0 * math.pi * radius_km * radius_km


def strip_mass(row: dict[str, str]) -> float:
    radius_m = float(row["radius_km"]) * 1000.0
    g = float(row["surface_gravity_m_s2"])
    d_m = min(STRIP_P_MAX / (EXCAVATION_RHO * g), radius_m)
    return 4.0 * math.pi * EXCAVATION_RHO * (
        radius_m * radius_m * d_m - radius_m * d_m * d_m + d_m**3 / 3.0
    )


def usable_fraction(row: dict[str, str], usability: dict[str, dict[str, str]]) -> float:
    entry = usability.get(row["body_id"])
    if not entry:
        return 1.0
    return float(entry["usable_fraction"])


def usable_strip_mass(row: dict[str, str], usability: dict[str, dict[str, str]]) -> float:
    return strip_mass(row) * usable_fraction(row, usability)


def leo_dv(row: dict[str, str]) -> float:
    return float(row["leo_delta_v_km_s"] or 0.0)


def group_rows(
    rows: list[dict[str, str]],
    value_fn,
    asteroid_threshold: float,
    bucket_label: str,
    bucket_color: str = "#9aa0a6",
) -> list[dict[str, object]]:
    rows = [r for r in rows if selected(r)]
    grouped: list[dict[str, object]] = []
    asteroid_bucket = []

    for r in rows:
        value = value_fn(r)
        if r["kind"] == "asteroid" and value < asteroid_threshold:
            asteroid_bucket.append(r)
            continue
        grouped.append(
            {
                "label": r["name"],
                "kind": r["kind"],
                "parent": r["parent"],
                "value": value,
                "share": 0.0,
                "leo_dv": leo_dv(r),
                "members": [r["name"]],
                "color": color_for_body(r["kind"], r["name"]),
            }
        )

    if asteroid_bucket:
        total = sum(value_fn(r) for r in asteroid_bucket)
        if total > 0:
            weighted_x = sum(value_fn(r) * leo_dv(r) for r in asteroid_bucket) / total
        else:
            weighted_x = 0.0
        grouped.append(
            {
                "label": bucket_label,
                "kind": "asteroid",
                "parent": "Sun",
                "value": total,
                "share": 0.0,
                "leo_dv": weighted_x,
                "members": [r["name"] for r in asteroid_bucket],
                "color": bucket_color,
            }
        )

    grouped.sort(key=lambda r: float(r["value"]), reverse=True)
    total_mass = sum(float(r["value"]) for r in grouped)
    for r in grouped:
        r["share"] = float(r["value"]) / total_mass if total_mass else 0.0
    return grouped


def color_for_kind(kind: str) -> str:
    return {
        "planet": "#2563eb",
        "moon": "#059669",
        "asteroid": "#7c3aed",
    }.get(kind, "#999999")


def stable_index(text: str, modulo: int) -> int:
    total = 0
    for ch in text:
        total = (total * 33 + ord(ch)) % 2_147_483_647
    return total % modulo


def color_for_body(kind: str, name: str) -> str:
    if name in BODY_COLOR_OVERRIDES:
        return BODY_COLOR_OVERRIDES[name]
    if kind == "planet":
        return PLANET_SHADES[stable_index(name, len(PLANET_SHADES))]
    if kind == "moon":
        return MOON_SHADES[stable_index(name, len(MOON_SHADES))]
    if kind == "asteroid":
        return ASTEROID_SHADES[stable_index(name, len(ASTEROID_SHADES))]
    return color_for_kind(kind)


def polar(cx: float, cy: float, r: float, angle: float) -> tuple[float, float]:
    return cx + r * math.cos(angle), cy + r * math.sin(angle)


def arc_path(cx: float, cy: float, r0: float, r1: float, a0: float, a1: float) -> str:
    x0, y0 = polar(cx, cy, r1, a0)
    x1, y1 = polar(cx, cy, r1, a1)
    x2, y2 = polar(cx, cy, r0, a1)
    x3, y3 = polar(cx, cy, r0, a0)
    large = 1 if a1 - a0 > math.pi else 0
    return (
        f"M {x0:.2f} {y0:.2f} "
        f"A {r1:.2f} {r1:.2f} 0 {large} 1 {x1:.2f} {y1:.2f} "
        f"L {x2:.2f} {y2:.2f} "
        f"A {r0:.2f} {r0:.2f} 0 {large} 0 {x3:.2f} {y3:.2f} Z"
    )


def svg_header(
    width: int,
    height: int,
    title: str,
    bg: str = "#f7f1e3",
    wheel: bool = False,
    scatter_large: bool = False,
) -> list[str]:
    title_size = 54 if wheel else (60 if scatter_large else 30)
    subtitle_size = 28 if wheel else (32 if scatter_large else 15)
    legend_size = 26 if wheel else (30 if scatter_large else 13)
    tick_size = 12 if wheel else (24 if scatter_large else 12)
    return [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        f"<title>{escape(title)}</title>",
        f'<rect width="100%" height="100%" fill="{bg}"/>',
        '<style><![CDATA[',
        'text { font-family: "Georgia", "Times New Roman", serif; fill: #2d2a26; }',
        f'.title {{ font-size: {title_size}px; font-weight: 700; }}',
        f'.subtitle {{ font-size: {subtitle_size}px; }}',
        f'.legend {{ font-size: {legend_size}px; }}',
        '.axis { stroke: #403a33; stroke-width: 2; fill: none; }',
        '.grid { stroke: #d8cec0; stroke-width: 1; }',
        f'.tick {{ font-size: {tick_size}px; }}',
        ']]></style>',
    ]


def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def compact_bucket_label(threshold: float, unit: str) -> str:
    if unit == "kg":
        return f"Asteroids < {threshold:.0e} kg"
    return f"Asteroids < {threshold:.0e} {unit}"


def render_wheel(
    groups: list[dict[str, object]],
    title: str,
    subtitle: str,
    bg: str,
    footer_note: str,
    legend_columns: int = 2,
) -> str:
    width, height = 1400, 900
    cx, cy = 390, 455
    r0, r1 = 120, 290
    angle = -math.pi / 2
    parts = svg_header(width, height, title, bg=bg, wheel=True)
    parts.append(f'<text class="title" x="70" y="70">{escape(title)}</text>')
    parts.append(f'<text class="subtitle" x="70" y="98">{escape(subtitle)}</text>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r0}" fill="#f7f1e3" stroke="#403a33" stroke-width="2"/>')

    visible_groups = [g for g in groups if float(g["share"]) > 0.0]
    legend_x = 760
    legend_rows = max(1, math.ceil(len(visible_groups) / legend_columns))
    legend_step = 40
    legend_block_height = (legend_rows - 1) * legend_step
    legend_y = cy - legend_block_height / 2.0
    legend_title_y = legend_y - 38
    for idx, g in enumerate(visible_groups):
        share = float(g["share"])
        a1 = angle + share * math.tau
        wobble = 1.0 + 0.03 * math.sin(idx * 2.7 + share * 12.0)
        outer = r1 * wobble
        parts.append(
            f'<path d="{arc_path(cx, cy, r0, outer, angle, a1)}" fill="{g["color"]}" stroke="#2d2a26" stroke-width="2"/>'
        )
        angle = a1

    parts.append(f'<text class="legend" x="{legend_x}" y="{legend_title_y:.1f}">Legend</text>')
    for idx, g in enumerate(visible_groups):
        col = idx % legend_columns
        row = idx // legend_columns
        tx = legend_x + col * 290
        ty = legend_y + row * legend_step
        parts.append(f'<rect x="{tx}" y="{ty-18}" width="18" height="18" fill="{g["color"]}" stroke="#2d2a26" stroke-width="1"/>')
        parts.append(f'<text class="legend" x="{tx+26}" y="{ty-3}">{escape(g["label"])} {float(g["share"]) * 100.0:.3f}%</text>')

    parts.append(f'<text x="{70}" y="{800}" class="subtitle">{escape(footer_note)}</text>')
    parts.append("</svg>")
    return "\n".join(parts)


def render_scatter(groups: list[dict[str, object]], title: str, subtitle: str) -> str:
    width, height = 1400, 900
    left, top, right, bottom = 120, 110, 100, 140
    plot_w = width - left - right
    plot_h = height - top - bottom

    visible_groups = [g for g in groups if float(g["value"]) > 0.0]
    xs = [float(g["leo_dv"]) for g in visible_groups]
    ys = [math.log10(float(g["value"])) for g in visible_groups]
    x_min, x_max = 0.0, max(xs) * 1.08
    y_min, y_max = min(ys) - 0.3, max(ys) + 0.3

    def sx(x: float) -> float:
        return left + (x - x_min) / (x_max - x_min) * plot_w

    def sy(y: float) -> float:
        return top + (y_max - y) / (y_max - y_min) * plot_h

    parts = svg_header(width, height, title, bg="#f4efe8", wheel=False, scatter_large=True)
    parts.append(f'<text class="title" x="175" y="68">{escape(title)}</text>')
    parts.append(f'<text class="subtitle" x="175" y="104">{escape(subtitle)}</text>')

    # Grid and axes.
    for tick in range(0, int(math.ceil(x_max)) + 1, 5):
        x = sx(tick)
        parts.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top+plot_h}" />')
        parts.append(f'<text class="tick" x="{x:.1f}" y="{top+plot_h+28}" text-anchor="middle">{tick}</text>')
    y_tick_start = math.floor(y_min)
    y_tick_end = math.ceil(y_max)
    for tick in range(y_tick_start, y_tick_end + 1):
        y = sy(tick)
        parts.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left+plot_w}" y2="{y:.1f}" />')
        parts.append(f'<text class="tick" x="{left-14}" y="{y+6:.1f}" text-anchor="end">1e{tick}</text>')
    parts.append(f'<line class="axis" x1="{left}" y1="{top+plot_h}" x2="{left+plot_w}" y2="{top+plot_h}" />')
    parts.append(f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top+plot_h}" />')
    parts.append(f'<text class="subtitle" x="{left + plot_w/2:.1f}" y="{height-48}" text-anchor="middle">Delta-v from LEO (km/s)</text>')
    parts.append(f'<text class="subtitle" transform="translate(36 {top + plot_h/2:.1f}) rotate(-90)" text-anchor="middle">Reachable mass (kg, log scale)</text>')

    for g in visible_groups:
        x = sx(float(g["leo_dv"]))
        y = sy(math.log10(float(g["value"])))
        color = g["color"]
        radius = 9 if not str(g["label"]).startswith("Asteroids < ") else 11
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius}" fill="{color}" stroke="#2d2a26" stroke-width="1.5"/>')
        label = g["label"]
        is_bucket = str(label).startswith("Asteroids < ")
        dx = -12 if x > width * 0.56 else 12
        anchor = "end" if dx < 0 else "start"
        dy = 16 if is_bucket else -10
        parts.append(f'<text class="legend" x="{x+dx:.1f}" y="{y+dy:.1f}" text-anchor="{anchor}">{escape(label)}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def write_summary(groups: list[dict[str, object]], path: Path) -> None:
    total = sum(float(g["value"]) for g in groups)
    asteroid_group = next((g for g in groups if str(g["label"]).startswith("Asteroids < ")), None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Visualization Summary\n\n")
        f.write("The reachable-mass wheel groups small asteroids into a compact `Asteroids < 1e17 kg` bucket.\n\n")
        if asteroid_group:
            f.write(f"Grouped asteroid tail mass: `{float(asteroid_group['value']):.6e} kg`\n\n")
        f.write(f"Total ordinary reachable mass used in the visualizations: `{total:.6e} kg`\n\n")
        f.write("| Label | Kind | Value | Share | LEO delta-v km/s |\n")
        f.write("| --- | --- | ---: | ---: | ---: |\n")
        for g in groups:
            f.write(
                f"| {g['label']} | {g['kind']} | {float(g['value']):.6e} | {float(g['share']):.4%} | {float(g['leo_dv']):.4g} |\n"
            )


def main() -> None:
    rows = load_rows(Path("data/derived/bodies_catalog.csv"))
    usability = load_usability(Path("data/definition/mining_surface_access.csv"))
    reachable_bucket = compact_bucket_label(ASTEROID_DETAIL_THRESHOLD_KG, "kg")
    area_bucket = compact_bucket_label(ASTEROID_DETAIL_THRESHOLD_AREA_KM2, "km^2")
    strip_bucket = compact_bucket_label(ASTEROID_DETAIL_THRESHOLD_KG, "kg")

    reachable_groups = group_rows(
        rows,
        mass,
        ASTEROID_DETAIL_THRESHOLD_KG,
        reachable_bucket,
    )
    area_groups = group_rows(
        rows,
        surface_area,
        ASTEROID_DETAIL_THRESHOLD_AREA_KM2,
        area_bucket,
        bucket_color="#9aa0a6",
    )
    strip_groups = group_rows(
        rows,
        strip_mass,
        ASTEROID_DETAIL_THRESHOLD_KG,
        strip_bucket,
    )
    usable_strip_groups = group_rows(
        rows,
        lambda r: usable_strip_mass(r, usability),
        ASTEROID_DETAIL_THRESHOLD_KG,
        strip_bucket,
    )

    write(
        Path("data/derived/ordinary_area_reference_wheel.svg"),
        render_wheel(
            area_groups,
            "Surface area reference",
            "XKCD-style surface area reference.",
            "#f7f1e3",
            "",
        ),
    )
    write(
        Path("data/derived/ordinary_reachable_mass_wheel.svg"),
        render_wheel(
            reachable_groups,
            "Reachable mass",
            "Mass share normalized to 100 percent across Mercury, Venus, Earth, Mars, their moons, and asteroids.",
            "#f7f1e3",
            "",
        ),
    )
    write(
        Path("data/derived/ordinary_strip_mining_mass_wheel.svg"),
        render_wheel(
            strip_groups,
            "Strip-mining mass",
            "Shallow, easily reachable mass using the low pressure cap calibrated to about 100 m of Earth depth.",
            "#f7f1e3",
            "",
        ),
    )
    write(
        Path("data/derived/usable_strip_mining_mass_wheel.svg"),
        render_wheel(
            usable_strip_groups,
            "Usable strip-mining mass",
            "Strip-mining mass with Earth land-only access and Venus removed from the usable surface pool.",
            "#f7f1e3",
            "",
        ),
    )
    write(Path("data/derived/ordinary_mass_wheel.svg"), Path("data/derived/ordinary_reachable_mass_wheel.svg").read_text())
    write(
        Path("data/derived/ordinary_area_reference_scatter.svg"),
        render_scatter(area_groups, "Surface area versus delta-v", "Surface area on a log scale, paired with LEO delta-v."),
    )
    write(
        Path("data/derived/ordinary_reachable_mass_scatter.svg"),
        render_scatter(reachable_groups, "Reachable mass versus delta-v", "Reachable mass on a log scale, paired with LEO delta-v."),
    )
    write(
        Path("data/derived/ordinary_strip_mining_mass_scatter.svg"),
        render_scatter(strip_groups, "Strip-mining mass versus delta-v", "Strip-mining mass on a log scale, paired with LEO delta-v."),
    )
    write(
        Path("data/derived/usable_strip_mining_mass_scatter.svg"),
        render_scatter(
            usable_strip_groups,
            "Usable strip-mining mass versus delta-v",
            "Earth keeps only its land fraction, Venus is zero, and zero-mass rows are omitted from the log plot.",
        ),
    )
    write(Path("data/derived/ordinary_delta_v_scatter.svg"), Path("data/derived/ordinary_reachable_mass_scatter.svg").read_text())
    write_summary(reachable_groups, Path("data/derived/visuals_summary.md"))
    print("wrote visuals")


if __name__ == "__main__":
    main()
