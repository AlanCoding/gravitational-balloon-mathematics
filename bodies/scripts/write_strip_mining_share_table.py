#!/usr/bin/env python3
"""Write a normalized share table for easily reachable strip-mining mass."""

from __future__ import annotations

import csv
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


def strip_mass_kg(row: dict[str, str]) -> float:
    radius_m = float(row["radius_km"]) * 1000.0
    g = float(row["surface_gravity_m_s2"])
    rho = float(row["excavation_rho_kg_m3"])
    d_m = min(P_MAX_PA / (rho * g), radius_m)
    return 4.0 * 3.141592653589793 * rho * (
        radius_m * radius_m * d_m - radius_m * d_m * d_m + d_m**3 / 3.0
    )


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    rows = [r for r in rows if selected(r)]
    rows.sort(key=strip_mass_kg, reverse=True)
    total = sum(strip_mass_kg(r) for r in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Ordinary Strip-Mining Share\n\n")
        f.write(
            "This table normalizes the easily reachable mass across the same ordinary subset "
            "as the main share table, but with a very low pressure cap calibrated to about 100 m of Earth depth.\n\n"
        )
        f.write(f"Pressure cap used here: `{P_MAX_PA:.3g} Pa`\n\n")
        f.write(f"Total strip-minable mass across this subset: `{total:.6e} kg`\n\n")
        f.write(
            "| Body | Kind | Parent | Strip-mineable mass kg | Share of total | Cumulative share | Delta-v from LEO km/s | Mass src | Radius src | Computed |\n"
        )
        f.write("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |\n")
        cumulative = 0.0
        for r in rows:
            mass = strip_mass_kg(r)
            share = mass / total if total else 0.0
            cumulative += share
            dv = r.get("leo_delta_v_km_s", "")
            f.write(
                f"| {r['name']} | {r['kind']} | {r['parent']} | {mass:.6e} | {share:.4%} | {cumulative:.4%} | {dv} | {r['mass_source_id']} | {r['radius_source_id']} | {r['reachable_mass_is_computed']} |\n"
            )
        f.write(f"\n| Total |  |  | `{total:.6e}` | `100.0000%` | `100.0000%` |  |  |  |  |\n")


def main() -> None:
    rows = load_rows(Path("data/derived/bodies_catalog.csv"))
    write_markdown(rows, Path("data/derived/strip_mining_share.md"))
    print("wrote strip_mining_share.md")


if __name__ == "__main__":
    main()
