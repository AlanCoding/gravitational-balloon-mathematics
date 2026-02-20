# Spherical Space Habitat: When the Pressure Wall Also Solves Heat Rejection + Radiation Shielding

This document defines the **equations**, **inequality constraints**, and **plot targets** for a Python CLI program.

Goal: For a **thin spherical pressure vessel** holding sea-level air, determine the radius ranges where:

1) **Heat rejection can be handled by the sphere’s exterior surface** (no added radiators), *while keeping inhabitants below a maximum allowed interior-wall temperature*.

2) **Radiation shielding areal mass requirement** is met by the wall itself (no added shielding).

The program will output “sweet spot” plots that compare an assumed design point (expected heat generation density) against the **maximum allowable** heat generation density as a function of radius.


---

## 1) Scope, assumptions, and boundary conditions

### Geometry
- Sphere radius: `R` [m]
- Wall thickness: `t` [m], with **thin-wall** assumption `t << R`

### Atmosphere / pressure vessel
- Internal pressure: `p` [Pa] (default 101325 Pa)
- Allowable membrane stress (already includes engineering margin): `σ_allow` [Pa]
- Density of wall material: `ρ` [kg/m³]

### Thermal
- Uniform volumetric heat generation inside the sphere: `q'''` [W/m³]
- Exterior radiates to space at background temperature `T_space` [K] (default 3 K, can be 0 K for first pass)
- Exterior surface emissivity: `ε` [-]
- Stefan–Boltzmann constant: `σ_SB = 5.670374419e-8` [W/m²/K⁴]
- Thermal conductivity of wall: `k` [W/m/K]
- Optional interior convection coefficient: `h_i` [W/m²/K] (set `h_i = +∞` to recover “inner surface fixed” style)

### Habitability temperature constraint
We enforce a **maximum allowable interior surface temperature**:
- `T_in_max` [K] (default near room temp, e.g. 303 K or 313 K, but this is an input)

Interpretation: “If the inner wall gets hotter than `T_in_max`, you are cooking the inhabitants / overloading HVAC.”


---

## 2) Core derived quantities

### 2.1 Pressure-dictated wall thickness
Thin spherical pressure vessel membrane stress:
\[
\sigma = \frac{pR}{2t}
\]
So the minimum thickness required for pressure:
\[
t_p(R) = \frac{pR}{2\sigma_{\text{allow}}}
\]

### 2.2 Heat flux at the wall from volumetric generation
Total heat:
\[
\dot Q = q''' \cdot \frac{4}{3}\pi R^3
\]
Surface area:
\[
A = 4\pi R^2
\]
Therefore the **average outward heat flux** at the wall is:
\[
q''(R) = \frac{\dot Q}{A} = \frac{q''' R}{3}
\]
This identity is very useful because it removes the big \(\pi\) terms.

---

## 3) Thermal resistances and temperatures

We treat heat transfer as a 1-D series from interior air → inner wall surface → through wall → outer wall surface → radiation to space.

### 3.1 Interior convection drop (optional)
If `h_i` is finite, the air-to-inner-wall temperature rise is:
\[
\Delta T_{\text{conv}} = \frac{q''}{h_i}
\]
If you want to ignore convection and treat the **inner surface temperature** directly, set `h_i = +∞` so \(\Delta T_{\text{conv}}=0\).

### 3.2 Conduction drop through wall
\[
\Delta T_{\text{cond}} = \frac{q'' t}{k}
\]
Using the pressure thickness \(t_p(R)\):
\[
\Delta T_{\text{cond}}(R) = \frac{q''(R)\, t_p(R)}{k}
= \frac{\left(\frac{q'''R}{3}\right)\left(\frac{pR}{2\sigma_{\text{allow}}}\right)}{k}
= \frac{q''' \, p \, R^2}{6k\sigma_{\text{allow}}}
\]
(Useful for sanity checking scaling: \(\Delta T_{\text{cond}} \propto q''' R^2\).)

### 3.3 Radiation boundary condition (outer surface)
Radiation to space:
\[
q'' = \varepsilon\sigma_{\text{SB}}\left(T_{\text{out}}^4 - T_{\text{space}}^4\right)
\]
So for a given flux \(q''\), the required outer surface temperature is:
\[
T_{\text{out}}(q'') =
\left(\frac{q''}{\varepsilon\sigma_{\text{SB}}} + T_{\text{space}}^4\right)^{1/4}
\]

### 3.4 Inner surface temperature
Starting from the outer surface:
\[
T_{\text{in,surf}} = T_{\text{out}} + \Delta T_{\text{cond}}
\]
If convection is included and you want the interior air temperature:
\[
T_{\text{air}} = T_{\text{in,surf}} - \Delta T_{\text{conv}}
\]
But for this program, the *habitability limit* will apply to:
- either `T_in_surf` (simplest), or
- `T_air` (slightly more realistic, if you supply `h_i`)

Choose one, but implement both and allow the user to select via a flag:
- `--temp_constraint_target inner_surface|air`

---

## 4) The key inequality: Maximum allowable volumetric heat generation `q'''_max(R)`

We want an inequality of the form:
\[
q''' \le q'''_{\max}(R)
\]
where exceeding \(q'''_{\max}\) would force `T_in,surf` (or `T_air`) above `T_in_max`.

### 4.1 “Inner surface” constraint (default)
Define:
\[
T_{\text{in,surf}}(R, q''') =
T_{\text{out}}\!\left(q''(R,q''')\right) + \Delta T_{\text{cond}}(R,q''')
\]
with:
- \(q'' = \frac{q'''R}{3}\)
- \(t = t_p(R)\)
- \(T_{\text{out}}(q'') = \left(\frac{q''}{\varepsilon\sigma_{\text{SB}}} + T_{\text{space}}^4\right)^{1/4}\)
- \(\Delta T_{\text{cond}} = \frac{q''t}{k}\)

Constraint:
\[
T_{\text{in,surf}}(R, q''') \le T_{\text{in,max}}
\]

This defines \(q'''_{\max}(R)\) implicitly as the value that makes it equality:
\[
T_{\text{in,surf}}(R, q'''_{\max}) = T_{\text{in,max}}
\]

**Implementation detail:** This equation is monotonic in \(q'''\) for reasonable parameter ranges, so solve with a 1-D root find (bisection/Brent):
- define \(f(q''') = T_{\text{in,surf}}(R,q''') - T_{\text{in,max}}\)
- find \(q'''_{\max}\) where \(f=0\)

### 4.2 Optional “air” constraint with `h_i`
If using interior convection:
\[
T_{\text{air}}(R,q''') =
T_{\text{out}}(q'') + \Delta T_{\text{cond}} - \Delta T_{\text{conv}}
=
T_{\text{out}}(q'') + \frac{q''t}{k} - \frac{q''}{h_i}
\]
Constraint:
\[
T_{\text{air}}(R,q''') \le T_{\text{air,max}}
\]
Solve similarly for \(q'''_{\max}(R)\).

---

## 5) “Expected” volumetric heat generation line from your population rule

You previously defined a design-point `q'''_expected` from:
- 1000 people per km³
- 23 kW per person

\[
q'''_{\text{expected}} = 0.023\ \text{W/m}^3
\]

The first sanity plot will show:
- x-axis: `R` (km)
- y-axis: `q'''_max(R)` (W/m³)
- horizontal line: `q'''_expected`
- “sweet spot” shading: where `q'''_max(R) >= q'''_expected`

Add a second optional horizontal line for a user-provided design density:
- `--qppp_expected` (W/m³)

---

## 6) Radiation shielding inequality (areal mass requirement)

We define the required shielding as an areal mass (mass thickness):
- `μ_req` [kg/m²], default corresponding to `2 tons/m² = 2000 kg/m²` (user input)

The wall’s areal mass is:
\[
\mu_{\text{wall}}(R)=\rho \, t(R)
\]

If the wall thickness is strictly pressure-dictated:
\[
\mu_{\text{wall}}(R) = \rho \, t_p(R) = \rho\frac{pR}{2\sigma_{\text{allow}}}
\]

Shielding sufficiency inequality:
\[
\mu_{\text{wall}}(R) \ge \mu_{\text{req}}
\]

This yields a simple radius threshold:
\[
R \ge R_{\text{shield}} =
\frac{2\sigma_{\text{allow}}\mu_{\text{req}}}{\rho p}
\]
(Use this for sanity checks; still compute and plot directly.)

Second plot:
- x-axis: `R` (km)
- y-axis: `μ_wall(R)` (kg/m²)
- horizontal line: `μ_req`
- shading: where `μ_wall(R) >= μ_req`

---

## 7) Combined “sweet spot” region

The “best” region is where both are satisfied:
1) Thermal: \(q'''_{\max}(R) \ge q'''_{\text{expected}}\)
2) Shielding: \(\mu_{\text{wall}}(R) \ge \mu_{\text{req}}\)

Make a combined plot (or combined shading on one plot):
- For each radius, compute booleans `ok_thermal`, `ok_shielding`
- Shade:
  - green: both true
  - yellow: thermal only
  - blue: shielding only
  - none: neither

Also print summary thresholds:
- minimum R where thermal passes for given expected q'''
- minimum R where shielding passes
- minimum R where both pass (if exists)

---

## 8) Inputs / defaults (CLI design)

Implement a CLI script, e.g. `hab_sphere.py`, with arguments:

### Physical inputs
- `--p` (Pa) default 101325
- `--sigma_allow` (Pa) default material-based
- `--rho` (kg/m³) default material-based
- `--k` (W/m/K) default material-based
- `--epsilon` default 0.2 (but user will sweep)
- `--T_space` (K) default 3
- `--T_in_max` (K) default 303 (or 313; pick one and document)
- `--h_i` (W/m²/K) default `inf` (meaning ignore interior convection)

### Design-point heat density
- `--q_expected` (W/m³) default 0.023

### Shielding requirement
- `--mu_req` (kg/m²) default 2000

### Radius sweep
- `--R_min_km` default 0.1
- `--R_max_km` default 200
- `--N` default 400
- `--R_scale` linear|log default log

### Material convenience presets
- `--material steel|al6061` sets (k, rho, sigma_allow) defaults:
  - steel: k=50, rho=7850, sigma_allow=125e6
  - al6061: k=170, rho=2700, sigma_allow=138e6

### Emissivity sweep
Support either:
- single `--epsilon 0.2`
or
- `--epsilon_list 0.1,0.2,0.9`

---

## 9) Numerical details (very explicit)

### 9.1 Compute pressure thickness and shielding
For each R:
- `t_p = p*R/(2*sigma_allow)`
- `mu_wall = rho*t_p`

### 9.2 Define temperature model function
Given `(R, qppp)`:
- `q_flux = qppp*R/3`
- `T_out = ((q_flux/(epsilon*sigma_SB)) + T_space**4)**0.25`
- `dT_cond = q_flux*t_p/k`
- `dT_conv = q_flux/h_i` (0 if h_i is inf)
- `T_in_surf = T_out + dT_cond`
- `T_air = T_in_surf - dT_conv`

### 9.3 Solve for qppp_max(R)
For each R, solve 1-D root:

If target = inner_surface:
- `f(qppp) = T_in_surf(R,qppp) - T_in_max`

If target = air:
- `f(qppp) = T_air(R,qppp) - T_in_max`

Root find:
- bracket with `q_low = 0`
- choose `q_high` by expanding (e.g. start `q_high=1e-3`, multiply by 2 until f(q_high)>0 or until a hard ceiling)
- bisection is fine and robust; Brent is nicer if available.
Return `qppp_max(R)`.

Sanity: if `f(q_high)` never becomes >0, then qppp_max is “very large” for this R (unlikely with realistic constraints); cap and report.

---

## 10) Plots to generate (objective outputs)

Use matplotlib (no seaborn). Do not set explicit colors unless needed for shading.

### Plot 1: Thermal allowable q''' vs R
- x: R (km)
- y: qppp_max(R) (W/m³)
- horizontal: q_expected
- shade: where qppp_max >= q_expected

If multiple epsilons, plot multiple curves and either:
- shade per epsilon separately (subplots NOT allowed per project preferences), or
- generate separate figures per epsilon.

### Plot 2: Shielding areal mass vs R
- x: R (km)
- y: mu_wall(R) (kg/m²)
- horizontal: mu_req
- shade: where mu_wall >= mu_req

### Plot 3: Combined feasibility map
Option A (recommended): a single figure with two y-axes:
- left y: qppp_max(R)
- right y: mu_wall(R)
- plus shaded regions by combined boolean status

Option B: separate “status” plot:
- y is categorical (0..3) or draw colored background bands; avoid making it confusing.

Save plots to `./out/` with filenames encoding material and epsilon, e.g.:
- `out/thermal_steel_eps0p2.png`
- `out/shielding_steel.png`
- `out/combined_steel_eps0p2.png`

Also write a CSV of computed arrays:
- columns: R_m, R_km, t_m, mu_wall, qppp_max, ok_thermal, ok_shielding, ok_both

---

## 11) Program structure (recommended)

Repo layout suggestion:
- `hab_sphere/`
  - `__init__.py`
  - `physics.py` (equations, temperature model)
  - `solve.py` (qppp_max solver)
  - `plots.py` (plot helpers)
  - `cli.py` (argparse + wiring)
- `out/` (generated artifacts, gitignored)
- `README.md` (brief usage + examples)
- `requirements.txt` (numpy, matplotlib)

Add minimal unit tests (optional but good):
- test that `q_flux == qppp*R/3`
- test that `t_p` scales linearly with R
- test that `mu_wall` threshold matches analytic `R_shield`

---

## 12) Notes / interpretation guards

- This model **does not** include: solar input, Earth IR/albedo, view factors, radiative fin efficiency, multilayer walls, internal convection complexity, or localized heat sources.
- This model **does** capture the essential coupled scaling:
  - heat generation \( \propto R^3 \)
  - radiating area \( \propto R^2 \)
  - pressure thickness \( \propto R \)
  - conduction drop \( \propto q''' R^2 \)
  - required radiating temperature rises as flux rises

This is exactly what we want for first publication: a clean scaling-driven feasibility map.

---

## 13) Example CLI runs (to include in README)

- Steel, epsilon 0.2:
  - `python -m hab_sphere.cli --material steel --epsilon 0.2 --T_in_max 303 --mu_req 2000 --q_expected 0.023`

- Aluminum, epsilon sweep:
  - `python -m hab_sphere.cli --material al6061 --epsilon_list 0.1,0.2,0.9 --T_in_max 303 --mu_req 2000 --q_expected 0.023`

- Include interior convection:
  - `python -m hab_sphere.cli --material steel --epsilon 0.2 --h_i 5 --temp_constraint_target air`

(Use `h_i` values only if you’re comfortable defending them; otherwise keep `h_i=inf`.)

---

## 14) Deliverables checklist (what the code MUST produce)

1) Thermal plot(s): `qppp_max(R)` with expected line and shaded “allowed”
2) Shielding plot: `mu_wall(R)` with required line and shaded “allowed”
3) Combined plot: shows where both conditions hold
4) CSV export of arrays
5) Printed summary of threshold radii for each constraint and combined
