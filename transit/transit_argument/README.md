# transit_argument

`transit_argument/` is a small Python subproject for two related outputs:

1. Real-network-ish transit reachability tables for six metro areas.
2. Thermal sufficiency calculations for two 1-billion-person space-city concepts.

The code favors concrete outputs and explicit approximations over a heavyweight planner stack.

## Folder structure

```text
transit_argument/
  data/raw/<city>/               # cached Overpass downloads
  outputs/tables/                # required CSV outputs
  outputs/diagnostics/           # anchor ranking + population diagnostics
  outputs/geojson/               # map-friendly station outputs
  scripts/                       # runnable entry points
  src/transit_argument/          # reusable modules
```

## Dependencies

- Python 3.11+
- `numpy`
- `pandas`

This project is intended to run with `~/venvs/gb/bin/python`.

## How to run

From the repository root:

```bash
~/venvs/gb/bin/python transit_argument/scripts/run_transit.py --city new_york --city london
~/venvs/gb/bin/python transit_argument/scripts/compute_thermal_bounds.py
~/venvs/gb/bin/python transit_argument/scripts/compute_vacuum_lattice.py
~/venvs/gb/bin/python transit_argument/scripts/build_project_summary.py
```

Or run everything:

```bash
~/venvs/gb/bin/python transit_argument/scripts/run_all.py
```

If you want to re-download transit raw inputs:

```bash
~/venvs/gb/bin/python transit_argument/scripts/run_transit.py --refresh
```

## Output locations

- Transit station times: `outputs/tables/station_times_<city>.csv`
- Transit reach curves: `outputs/tables/reachable_population_curve_<city>.csv`
- Sphere thermal bounds: `outputs/tables/macrohabitat_sphere_thermal_bounds.csv`
- Lattice sky fraction: `outputs/tables/vacuum_lattice_sky_fraction_vs_spacing.csv`
- Lattice thermal summary: `outputs/tables/vacuum_lattice_thermal_summary.csv`
- Cross-project summary: `outputs/tables/project_summary.csv`

## Transit assumptions

- Network source: OpenStreetMap route relations and station objects downloaded through Overpass.
- Routing model: static weighted graph with in-vehicle time approximated from inter-station distance and mode-specific average speed.
- Penalties: explicit entry, exit, and transfer penalties from `src/transit_argument/config.py`.
- Walking links: added between stations within a short distance threshold to allow interchanges not encoded cleanly in route relations.
- Population attachment: fallback grid-based density surface shaped by station kernels and normalized to a configured metro population total.

This is intentionally not a timetable-accurate GTFS router. It is a transparent approximation that still respects real network topology, rivers, harbors, and line structure much better than straight-line access curves.

## Thermal assumptions

- Waste heat is `20 kW` per person.
- Sphere case uses pure Stefan-Boltzmann blackbody rejection from the outer sphere wall.
- Lattice case uses spherical habitats on a cubic lattice.
- Open-sky fraction is estimated by Monte Carlo ray casting from habitat surface points into the outward hemisphere.
- The lattice thermal sufficiency check multiplies total habitat surface area by the estimated clear-sky fraction to get an outer-bound style aggregate radiator capacity.
