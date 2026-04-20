from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transit_argument.config import TABLE_DIR
from transit_argument.io_utils import write_dataframe


def _collect_transit_rows() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for curve_path in sorted(TABLE_DIR.glob("reachable_population_curve_*.csv")):
        city_slug = curve_path.stem.removeprefix("reachable_population_curve_")
        station_path = TABLE_DIR / f"station_times_{city_slug}.csv"
        if not station_path.exists():
            continue
        curve = pd.read_csv(curve_path)
        station = pd.read_csv(station_path)
        if curve.empty or station.empty:
            continue
        sixty = curve[curve["minutes"] == 60]
        one_twenty = curve[curve["minutes"] == 120]
        city_name = str(curve.iloc[0]["city"])
        best_anchor = str(station["best_anchor"].dropna().iloc[0]) if station["best_anchor"].dropna().any() else ""
        rows.append(
            {
                "section": "transit",
                "subject": city_name,
                "metric_a": "reachable_population_60min",
                "value_a": float(sixty["reachable_population"].iloc[0]) if not sixty.empty else None,
                "metric_b": "reachable_population_120min",
                "value_b": float(one_twenty["reachable_population"].iloc[0]) if not one_twenty.empty else None,
                "notes": f"anchor={best_anchor}; stations={len(station)}",
            }
        )
    return rows


def main() -> None:
    rows: list[dict[str, object]] = []
    rows.extend(_collect_transit_rows())

    sphere_path = TABLE_DIR / "macrohabitat_sphere_thermal_bounds.csv"
    sphere = pd.read_csv(sphere_path) if sphere_path.exists() else pd.DataFrame()
    if not sphere.empty:
        coolest = sphere.sort_values("required_radius_m").iloc[0]
        rows.append(
            {
                "section": "thermal_sphere",
                "subject": "1B-person breathable sphere",
                "metric_a": "best_case_surface_temperature_K",
                "value_a": coolest["surface_temperature_K"],
                "metric_b": "required_radius_m",
                "value_b": coolest["required_radius_m"],
                "notes": "Blackbody sphere outer surface requirement",
            }
        )

    lattice_path = TABLE_DIR / "vacuum_lattice_thermal_summary.csv"
    lattice = pd.read_csv(lattice_path) if lattice_path.exists() else pd.DataFrame()
    if not lattice.empty:
        qualifying = lattice[lattice["threshold_met"] == True].sort_values("lattice_spacing_m")
        selected = qualifying.iloc[0] if not qualifying.empty else lattice.sort_values("lattice_spacing_m").iloc[-1]
        rows.append(
            {
                "section": "thermal_lattice",
                "subject": "1B-person habitat lattice",
                "metric_a": "selected_spacing_m",
                "value_a": selected["lattice_spacing_m"],
                "metric_b": "thermal_margin_vs_load",
                "value_b": selected["thermal_margin_vs_load"],
                "notes": "First spacing meeting open-sky threshold, else widest tested spacing",
            }
        )

    mobility_path = TABLE_DIR / "space_city_trip_summary.csv"
    mobility = pd.read_csv(mobility_path) if mobility_path.exists() else pd.DataFrame()
    if not mobility.empty:
        for row in mobility.to_dict("records"):
            rows.append(
                {
                    "section": "space_city_mobility",
                    "subject": row["case"],
                    "metric_a": "median_travel_time_min",
                    "value_a": row["median_travel_time_min"],
                    "metric_b": "p90_travel_time_min",
                    "value_b": row["p90_travel_time_min"],
                    "notes": f"mean_net_kinetic_energy_kwh={row['mean_net_kinetic_energy_kwh']:.3f}",
                }
            )

    write_dataframe(TABLE_DIR / "project_summary.csv", pd.DataFrame(rows))


if __name__ == "__main__":
    main()
