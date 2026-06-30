# Mining the Solar System

This folder is the starting point for XKCD-style visualizations about how much
material is reachable for future O'Neill-style industry.

The original reference is XKCD 1389:

- https://xkcd.com/1389/

The old comic maps planets and moons to flat land area. This project pivots the
same visual language toward mineable mass.

## Core Idea

For each body, we care about a shallow accessible shell rather than the whole
object.

Two first-order limits control the shell thickness:

- pressure limit: rock closes, crushes, or becomes too hard to excavate
- temperature limit: rock softens or excavation becomes impractical

The usable mining depth is:

```text
d_use = min(d_pressure, d_temperature, R)
```

where `R` is the body's mean radius.

In practice this project uses three closely related scenarios:

1. Reachable mass: the main shell model with pressure, temperature, and radius limits, used for the first set of mass tables and charts.
2. Strip-mining mass: a much shallower version of the same shell model, with a low pressure cap calibrated to about 100 m of Earth depth. This is meant to show the easily skimmed outer shell rather than deeper mining.
3. Usable strip-mining mass: the same shallow strip-mining case, but with unusable surface removed from the accessible area. In this version Earth only counts its land fraction and Venus is treated as completely unusable.

The pressure limit written below is the main calibration for the first and
second scenarios. The third scenario adds a separate usability factor on top of
that pressure-limited shell.

## Simplified Depth Model

Assume constant bulk density `rho` and near-surface gravity `g`.

### Pressure limit

Approximate lithostatic pressure as:

```text
P(z) = rho * g * z
```

If `P_max` is the maximum acceptable overburden pressure, then:

```text
d_pressure = P_max / (rho * g)
```

This is the calibration knob that should land Earth near the mining depths
that existing deep mines suggest, on the order of 1 mile when `P_max` is set
conservatively. It is the shared pressure calibration for both the reachable
mass and strip-mining scenarios; the usable strip-mining variant layers a
surface-availability assumption on top of the same shell model.

Important: `rho` in the depth model is the local excavation density, not always
the global bulk density of the body. For Earth and other differentiated worlds,
use a crust-like density for the accessible shell while keeping the bulk mass
column for the visualizations.

### Temperature limit

With surface temperature `T_s` and geothermal gradient `Gamma`:

```text
T(z) = T_s + Gamma * z
```

If `T_max` is the maximum workable temperature:

```text
d_temperature = (T_max - T_s) / Gamma
```

### Accessible mass

Treat the reachable volume as a spherical shell of thickness `d_use`.

```text
M_reachable = 4 * pi * rho * (R^2 * d_use - R * d_use^2 + d_use^3 / 3)
```

For `d_use << R`, the shell-mass approximation is:

```text
M_reachable approx 4 * pi * R^2 * rho * d_use
```

This is the quantity that should drive the strip-mining visual.

## Units

Use SI units internally:

- `R` in meters
- `rho` in kg/m^3
- `g` in m/s^2
- `P_max` in Pascals
- `T` in Kelvin or Celsius, as long as the difference is consistent

For DASTCOM5 asteroid records:

- `GM` is stored in `km^3 / s^2`
- mass is recovered by `M = GM / G`, with `GM` converted to SI first
- `RAD` is the mean radius in km

## Data Layout

The catalog is now split into layers:

- `data/origin/` contains source-truth inputs and source manifests
- `data/definition/` contains the curated body records
- `data/derived/` contains generated catalogs and preview tables

The current source-of-truth inputs are:

- `data/origin/sources.csv`
- `data/origin/asteroids_dastcom5_reference.csv`
- `data/origin/orbital_elements.csv`

The curated definition layer is:

- `data/definition/bodies_reference.csv`

The derived catalog is:

- `data/derived/bodies_catalog.csv`
- `data/derived/reachable_mass_share.md`

The extractor `scripts/extract_dastcom5.py` reads the local asteroid binary and
writes the origin-layer asteroid CSV plus preview tables. The generator
`scripts/build_body_catalog.py` combines the definition layer into the derived
catalog and emits a compact preview.

The `orbit_delta_v_km_s` column is an orbit-only transfer proxy, while
`leo_delta_v_km_s` is the column used in the main tables and is meant to
approximate travel from low Earth orbit:

- heliocentric bodies use a Hohmann-style transfer from Earth’s orbit plus a plane-change term, then a LEO departure term and a small arrival bonus
- Mars and the Mars moons use the Mars transfer proxy plus LEO departure, with perfect aerobraking assumed at Mars arrival
- Mercury and Earth's Moon use a full no-aerobraking landing term instead of the smaller conservative arrival bonus; the Moon case uses a simple LEO-to-lunar-transfer baseline first
- other moons add the parent-system transfer leg when needed, then the local moon transfer and arrival bonus
- Earth is fixed to `0 km/s` as the local reference body

It is a comparison metric, not a full mission-design solution.

The current race-to-the-answer artifact is
`data/derived/reachable_mass_share.md`. It normalizes minable mass to 100%
across the ordinary reachable subset only:

- Mercury
- Venus
- Earth
- Mars
- Earth/Mars moons
- asteroids

Gas giants and outer-system bodies are excluded from that table.

The strip-mining counterpart is `data/derived/strip_mining_share.md`. It uses
a much lower pressure cap calibrated to roughly 100 m of Earth depth, so Earth
falls to about a quarter of the total and the table shifts toward bodies where
only the very shallow shell is easy to reach.

The third case is `data/derived/usable_strip_mining_share.md`. It keeps the
same shallow-pressure model, but removes unusable surface: Earth is counted at
its land fraction and Venus is set to zero usable surface.

The browsable markdown table is:

- [data/derived/usable_strip_mining_share.md](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/usable_strip_mining_share.md)

The first visualization pass is in:

- [data/derived/ordinary_area_reference_wheel.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_area_reference_wheel.svg)
- [data/derived/ordinary_area_reference_scatter.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_area_reference_scatter.svg)
- [data/derived/ordinary_reachable_mass_wheel.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_reachable_mass_wheel.svg)
- [data/derived/ordinary_reachable_mass_scatter.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_reachable_mass_scatter.svg)
- [data/derived/ordinary_strip_mining_mass_wheel.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_strip_mining_mass_wheel.svg)
- [data/derived/ordinary_strip_mining_mass_scatter.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/ordinary_strip_mining_mass_scatter.svg)
- [data/derived/usable_strip_mining_mass_wheel.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/usable_strip_mining_mass_wheel.svg)
- [data/derived/usable_strip_mining_mass_scatter.svg](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/usable_strip_mining_mass_scatter.svg)
- [data/derived/visuals_summary.md](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/visuals_summary.md)
- [data/derived/visuals.md](/home/arominge/repos/gravitational-balloon-mathematics/bodies/data/derived/visuals.md)

For readability, the wheel charts use color-only wedges and a side legend.
Small asteroids are grouped into compact `Asteroids < ...` buckets in each
wheel. Each scatter uses the same grouped inputs as its matching wheel. The
usable strip-mining scatter omits zero-mass rows so the log scale stays valid.
Open dashed markers in the scatter plots mark the Mars-system no-aerobraking
references. Those markers are derived from a simple propulsive Mars capture
and descent estimate from LEO, not from a fixed visual offset.

At the moment only 17 asteroid records in the local dump have both `GM` and
`RAD` populated, so the asteroid preview table is intentionally small.

## Roadmap

1. Build a normalized body catalog for planets, moons, and asteroids.
2. Add derived columns for gravity, pressure-limited depth, and temperature-limited depth.
3. Reproduce the XKCD 1389 area-style visualization as a reference panel.
4. Add the mass-reachable visual for the full shell model.
5. Add a conservative strip-mining visual using a very shallow pressure cap.
6. Add a usable-surface strip-mining variant that excludes Earth oceans and Venus.
7. Expand asteroid coverage from the JPL database and rank bodies by reachable mass.

## Calibration Notes

Earth should be used as the sanity check.

With a conservative pressure cap around 40 MPa and a representative crustal
density, the model should return a practical depth close to 1 mile, which is
the right order of magnitude for deep mining.

Temperature can be made non-limiting on Earth by choosing a higher thermal cap;
that keeps the first pass simple and makes pressure the dominant bound.

See `data/calibration_table.md` for a few concrete values.
