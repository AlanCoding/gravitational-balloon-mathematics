#!/usr/bin/env python3
"""Write a normalized share table for strip-mining mass with unusable surfaces removed."""

from __future__ import annotations

import csv
import math
from pathlib import Path


ORDINARY_PLANETS = {"Mercury", "Venus", "Earth", "Mars"}
ORDINARY_MOONS = {"Earth", "Mars"}

# Calibrated to roughly 100 m of Earth depth with excavation density 3000 kg/m^3.
P_MAX_PA = 2.95e6


def load_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def selected(row: dict[str, str]) -> bool:
    kind = row["kind"]
    if kind == "planet":
        return row["name"] in ORDINARY_PLANETS
    if kind == "moon":
        return row["parent"] in ORDINARY_MOONS
    if kind == "asteroid":
        return True
    return False


def load_usability(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as f:
        return {row["body_id"]: row for row in csv.DictReader(f)}


def usable_fraction(row: dict[str, str], usability: dict[str, dict[str, str]]) -> float:
    entry = usability.get(row["body_id"])
    if not entry:
        return 1.0
    return float(entry["usable_fraction"])


def strip_mass_kg(row: dict[str, str], usability: dict[str, dict[str, str]]) -> float:
    radius_m = float(row["radius_km"]) * 1000.0
    g = float(row["surface_gravity_m_s2"])
    rho = float(row["excavation_rho_kg_m3"])
    d_m = min(P_MAX_PA / (rho * g), radius_m)
    base_mass = 4.0 * math.pi * rho * (
        radius_m * radius_m * d_m - radius_m * d_m * d_m + d_m**3 / 3.0
    )
    return base_mass * usable_fraction(row, usability)


def write_markdown(rows: list[dict[str, str]], usability: dict[str, dict[str, str]], path: Path) -> None:
    rows = [r for r in rows if selected(r)]
    rows.sort(key=lambda r: strip_mass_kg(r, usability), reverse=True)
    total = sum(strip_mass_kg(r, usability) for r in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Usable Strip-Mining Share\n\n")
        f.write(
            "This table extends the strip-mining case by removing unusable surface from the accessible mass. "
            "Earth keeps only its land fraction, while Venus is set to zero usable surface in this model.\n\n"
        )
        f.write(f"Pressure cap used here: `{P_MAX_PA:.3g} Pa`\n\n")
        f.write(f"Total usable strip-minable mass across this subset: `{total:.6e} kg`\n\n")
        f.write(
            "| Body | Kind | Parent | Strip-mineable mass kg | Usable surface fraction | Usability src | Share of total | Cumulative share | Delta-v from LEO km/s | Mass src | Radius src | Computed |\n"
        )
        f.write("| --- | --- | --- | ---: | ---: | --- | ---: | ---: | ---: | --- | --- | --- |\n")
        cumulative = 0.0
        for r in rows:
            mass = strip_mass_kg(r, usability)
            share = mass / total if total else 0.0
            cumulative += share
            dv = r.get("leo_delta_v_km_s", "")
            u = usability.get(r["body_id"])
            fraction = usable_fraction(r, usability)
            source_id = u["source_id"] if u else "default_full_surface"
            f.write(
                f"| {r['name']} | {r['kind']} | {r['parent']} | {mass:.6e} | {fraction:.4%} | {source_id} | {share:.4%} | {cumulative:.4%} | {dv} | {r['mass_source_id']} | {r['radius_source_id']} | 1 |\n"
            )
        f.write(f"\n| Total |  |  | `{total:.6e}` | `100.0000%` |  | `100.0000%` | `100.0000%` |  |  |  |  |\n")


def main() -> None:
    rows = load_rows(Path("data/derived/bodies_catalog.csv"))
    usability = load_usability(Path("data/definition/mining_surface_access.csv"))
    write_markdown(rows, usability, Path("data/derived/usable_strip_mining_share.md"))
    print("wrote usable_strip_mining_share.md")


if __name__ == "__main__":
    main()
