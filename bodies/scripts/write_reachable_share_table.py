#!/usr/bin/env python3
"""Write a normalized reachable-mass share table for ordinary bodies."""

from __future__ import annotations

import csv
from pathlib import Path


ORDINARY_PLANETS = {"Mercury", "Venus", "Earth", "Mars"}
ORDINARY_MOONS = {"Earth", "Mars"}


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


def write_markdown(rows: list[dict[str, str]], path: Path) -> None:
    rows = [r for r in rows if selected(r)]
    rows.sort(key=lambda r: float(r["reachable_mass_kg"]), reverse=True)
    total = sum(float(r["reachable_mass_kg"]) for r in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Ordinary Reachable Mass Share\n\n")
        f.write(
            "This table normalizes the minable mass across ordinary reachable bodies only: "
            "Mercury, Venus, Earth, Mars, Earth/Mars moons, and asteroids. Gas giants and outer-system bodies are excluded.\n\n"
        )
        f.write(f"Total reachable mass across this subset: `{total:.6e} kg`\n\n")
        f.write(
            "| Body | Kind | Parent | Reachable mass kg | Share of total | Cumulative share | Delta-v from LEO km/s | Mass src | Radius src | Computed |\n"
        )
        f.write("| --- | --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |\n")
        cumulative = 0.0
        for r in rows:
            mass = float(r["reachable_mass_kg"])
            share = mass / total if total else 0.0
            cumulative += share
            dv = r.get("leo_delta_v_km_s", "")
            f.write(
                f"| {r['name']} | {r['kind']} | {r['parent']} | {mass:.6e} | {share:.4%} | {cumulative:.4%} | {dv} | {r['mass_source_id']} | {r['radius_source_id']} | {r['reachable_mass_is_computed']} |\n"
            )
        f.write(f"\n| Total |  |  | `{total:.6e}` | `100.0000%` | `100.0000%` |  |  |  |  |\n")


def main() -> None:
    rows = load_rows(Path("data/derived/bodies_catalog.csv"))
    write_markdown(rows, Path("data/derived/reachable_mass_share.md"))
    print("wrote reachable_mass_share.md")


if __name__ == "__main__":
    main()
