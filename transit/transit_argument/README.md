# transit_argument

`transit_argument/` is a small Python subproject for three related outputs:

1. Real-network-ish transit reachability tables for six metro areas.
2. Thermal sufficiency calculations for two 1-billion-person space-city concepts.
3. Reachable-population-vs-time curves for two 1-billion-person space-city mobility concepts.

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
~/venvs/gb/bin/python transit_argument/scripts/compute_space_city_mobility.py
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
- Space-city reach curves: `outputs/tables/reachable_population_curve_space_city_<case>.csv`
- Space-city mobility summary: `outputs/tables/space_city_trip_summary.csv`
- Space-city vehicle tiers: `outputs/tables/space_city_tiers.csv`
- Atmosphere channel thermal check: `outputs/tables/space_city_atmosphere_channel_thermal.csv`
- Space-city plot: `outputs/plots/space_city_reachable_population_vs_time.png`
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

## Space-city mobility assumptions

- Movement is restricted to x/y/z lattice corridors only.
- The wheel-in-atmosphere case uses `1,000` people per wheel and a `100 x 100 x 100` wheel lattice.
- The vacuum case uses `10,000` people per habitat and a near-cubic occupied block containing `100,000` habitats.
- Tiered bus lines use nested spans so every trip remains traversible.
- The vacuum case models a single-person shielded pod that docks into larger electromagnetic buses.
- Reach curves are computed from a representative central origin, which is a reasonable proxy in a regular lattice city.
- Transfer penalties are hand-wavy but anchored to Earth metro interchange behavior and kept explicit in the config and outputs.
- The atmosphere case also includes a one-channel thermal check using the waste heat from one full line of adjacent habitats and the air mass flow through a square channel.
