# Spherical Habitat Feasibility Plots

CLI + plotting utilities for a thin spherical pressure vessel feasibility check with:

- Thermal limit: solve for `qppp_max(R)` under `T_in_max`
- Shielding limit: check `mu_wall(R) >= mu_req`
- Combined feasibility map: thermal, shielding, both

## Install

```bash
python -m pip install -r requirements.txt
```

## Example runs

```bash
python -m hab_sphere.cli --material steel --epsilon 0.8 --T_in_max 303 --mu_req 2000 --q_expected 0.023
python -m hab_sphere.cli --material al6061 --epsilon_list 0.1,0.2,0.9 --T_in_max 303 --mu_req 2000 --q_expected 0.023
python -m hab_sphere.cli --material steel --epsilon 0.2 --h_i 5 --temp_constraint_target air
```

## Numeric solver (no plots)

Use this to print crossover radii as plain numbers across all materials:

```bash
python -m hab_sphere.numeric_summary --epsilon 0.8 --q_expected 0.023 --mu_req 2000
```

Or sweep emissivity:

```bash
python -m hab_sphere.numeric_summary --epsilon_list 0.2,0.8,0.9
```

This prints, for each material and epsilon:

- shielding crossover radius (minimum `R` to satisfy `mu_wall >= mu_req`)
- thermal feasible interval at `q_expected`
- combined feasible interval where both constraints are satisfied
- validity guard: `R_min_km` is enforced to be at least `0.1` km (100 m)

## Total Q sanity plot

This script checks whether total heat ever reaches a maximum then declines as `R` increases.
It plots:

- `Q_expected = q_expected * (4/3) * pi * R^3`
- `Q_allowable = qppp_max(R) * (4/3) * pi * R^3`

and prints whether a peak-then-decline is detected for `Q_allowable` over the scanned range.

```bash
python -m hab_sphere.q_total_sanity --material steel --epsilon 0.8 --T_in_max 303 --q_expected 0.023
```

Default radius scan for this script is `10 km` to `10,000 km` (override with `--R_min_km` and `--R_max_km`).

## Outputs

By default, each run now writes to a material-specific folder:

- `steel/`
- `al6061/`

Each material folder contains:

- `thermal_<material>_eps<epsilon>.png`
- `shielding_<material>.png`
- `combined_<material>_eps<epsilon>.png`
- `results_<material>_eps<epsilon>.csv`
- `README.md` (embedded image report for quick viewing)

## Navigation

GitHub links to output folders:

- [steel](steel/README.md)
- [al6061](al6061/README.md)
