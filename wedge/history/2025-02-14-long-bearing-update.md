# Long-Bearing Radial Force Update — 2025‑02‑14

## Overview

Today’s session replaced the short-bearing approximation used in the laminar wedge model with the long-bearing (Sommerfeld) formulation described in `lit/radial.md`, and set up a reproducible Python environment for the wedge tools.

## Key changes

1. **Long-bearing solver (`wedge/positional_250.py`)**
   - Introduced a θ-grid and numerical integration helpers (with SciPy fallbacks) to integrate the 1D Reynolds equation for each gap.
   - Added `_long_bearing_radial_force`, which:
     * Sets the proper load scale `6 μ ΔU R`.
     * Solves for `p(θ)` via cumulative integration of `h^3 dp/dθ = 6 μ ΔU R dh/dθ`, enforcing periodicity and removing mean pressure.
     * Applies a Reynolds boundary (clips negative pressures) before projecting onto the radial axis, which produces realistic radial restoring forces.
   - Replaced the defunct short-bearing expressions in `gap_force_magnitudes` with the new radial solver and the tangential shear term from `lit/tangental.md`.
   - Updated `gap_force_vector`/`total_fluid_forces` to pass each gap’s inner radius to the new solver so the force scale uses the correct geometry.

2. **Validation**
   - Reran `wedge/sim_250.py` (headless via Agg) to ensure the long-bearing forces generate sensible `F_r` vs `F_θ` curves.
   - Spot-checked the new `gap_force_magnitudes` for several offsets (0.1–3 m) to confirm `F_r / F_θ` behaves as expected (~−0.01 to −10 instead of ~1e−14).

3. **Python environment**
   - Created a new virtual environment at `~/venvs/gb`.
   - Added `wedge/requirements.txt` listing `numpy`, `matplotlib`, and `scipy`, and installed them into the new venv (reran `pip install` with network access after the sandboxed attempt failed).

## Notes & follow-ups

* The cavitation boundary makes the radial force finite and roughly proportional to the positive-pressure arc length; you can revisit this clipping if you later model vapor pressure/air entrainment explicitly.
* All wedge scripts (`sim_250.py`, `time_sim_250.py`, etc.) now consume the updated `gap_force_magnitudes` automatically, so their outputs reflect the long-bearing physics.
* Activate the environment with `source ~/venvs/gb/bin/activate` before running the simulations; `pip install -r wedge/requirements.txt` keeps dependencies consistent if new ones are added.

Let me know if you want additional plots or history entries when you extend the model further.
