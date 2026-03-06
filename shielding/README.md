# Chevron Shielding Monte Carlo

This folder contains scripts to evaluate a repeating chevron shielding geometry and compare it to a flat reference wall.

## Files

- `monte_carlo_chevron.py`: Monte Carlo transmission model + solvers.
- `chevron_geometry_svg.py`: SVG geometry/ray visualizer with dimension labels.
- `PROMPT.md`: original problem framing.

## Final Agreed Framing

The final configuration used for the reported figure of merit is:

- Slat angle fixed at `theta = 45 deg`
- Depth fixed at `L = 1`
- Pitch fixed at `p = 0.5` (closure geometry for 45-degree chevrons)
- Model: `surface` (no true geometric slat thickness; attenuation uses crossing angle)
- Flat reference wall thickness: `d = 1`
- Flat reference optical depth: `tau_flat = 5`
- Calibration: `tau_reference = slab` so `lambda = tau_flat / d = 5`

Then solve for chevron attenuation thickness `t` such that:

- `T_chevron ~= T_flat`
- with no misses (`P_no_hit = 0`)

## Reproduce Final Solve

Run:

```bash
~/venvs/gb/bin/python monte_carlo_chevron.py \
  --model surface \
  --L 1 \
  --pitch 0.5 \
  --theta-deg 45 \
  --tau-reference slab \
  --solve-thickness-for-flat \
  --enforce-no-miss \
  --require-no-hit \
  --samples 800000 \
  --t-min 1e-5 \
  --t-max 2.0
```

Representative result:

- solved `t = 0.764942764022`
- `P_no_hit = 0`
- `T_flat = 0.001755601786`
- `T_chevron = 0.001755601718`
- hit-count diagnostics (also printed each run): `P_hit_0 ... P_hit_5`, `P_hit_6plus`, `mean_hits`

## Figure of Merit

Using the requested analytical geometric factor:

- `M = 2*sqrt(2) = 2.828427124746`
- `M' = t*M`

With solved `t`:

- `M' = 2.163584862637`

This is the current ultimate FOM for the agreed setup.

## One-Sided Extension Geometry

A new geometry mode is available:

- `model=surface_extended`
- `--center-extension-frac f` extends each segment on one side (toward center) by `f*L`
- `f=0.25` corresponds to `+50%` line-length material vs baseline chevron geometry

Example comparison at fixed `L=1`, `p=0.5`, `theta=45 deg`, no-miss enforcement, matching `T_flat` by solving `t`:

Baseline:

```bash
~/venvs/gb/bin/python monte_carlo_chevron.py \
  --model surface --L 1 --pitch 0.5 --theta-deg 45 --tau-reference slab \
  --solve-thickness-for-flat --enforce-no-miss --require-no-hit \
  --samples 400000 --t-min 1e-5 --t-max 2.0
```

- `t ~= 0.7648`
- `M_geom ~= 2.8284`
- `M_prime_geom_t ~= 2.1632`

Extended (`f=0.25`):

```bash
~/venvs/gb/bin/python monte_carlo_chevron.py \
  --model surface_extended --center-extension-frac 0.25 \
  --L 1 --pitch 0.5 --theta-deg 45 --tau-reference slab \
  --solve-thickness-for-flat --enforce-no-miss --require-no-hit \
  --samples 400000 --t-min 1e-5 --t-max 2.0
```

- `t ~= 0.3482`
- `M_geom ~= 4.2426`
- `M_prime_geom_t ~= 1.4773`

So this extension mode improved the final material factor (`M'`) for this scenario.

### Hit-Count Output

For `surface` and `surface_extended` models, `monte_carlo_chevron.py` now prints:

- `P_hit_0`, `P_hit_1`, ..., `P_hit_5`
- `P_hit_6plus`
- `mean_hits`

This makes it easy to verify whether one-hit paths dominate transmission for a given geometry.

## Geometry SVG

To generate a dimensioned SVG with sample rays and per-ray evaluated material path (`Lmat`):

```bash
~/venvs/gb/bin/python chevron_geometry_svg.py \
  --model surface \
  --L 1 \
  --pitch 0.5 \
  --thickness 0.764942764022 \
  --theta-deg 45 \
  --enforce-no-miss \
  --num-rays 16 \
  --out chevron_geometry.svg
```

Embedded preview:

![Chevron Geometry](chevron_geometry.svg)
