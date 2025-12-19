# 2025-12-17 – Pressure resultant replaces line-of-centers force

## Summary
- replaced the “radial/tangential” force pair with the full pressure resultant obtained from the long-bearing Reynolds integral (projected onto both cosθ and sinθ).
- removed the Couette shear term from the translational force calculation and kept it exclusively for torque/energy-loss modelling.
- added gap-index context to clearance violations so abort messages identify which shells collided.
- implemented an adaptive RK4 fallback that halves `dt` when a step fails because a gap approaches its clearance limit, letting the rapidly growing pressure force act before the solver aborts.

## Implementation notes
- `positional_250.py`
  - `_long_bearing_radial_force` was replaced by `_long_bearing_pressure_components`, returning both projections of the Reynolds pressure field.
  - `gap_force_magnitudes` / `gap_force_vector` now use that vector result directly; shear drag is no longer misinterpreted as a tangential net force.
  - `total_fluid_forces` now re-raises clearance errors with the gap index for better diagnostics.
- `multi_shell_time_sim.py`
  - added `rk4_step_adaptive` to recursively halve the time step when a ValueError occurs inside RK4 (typically from a clearance breach).
  - the main loop now uses this adaptive integrator, so strong pressure gradients near contact slow the dynamics rather than immediately crashing the run.
- `README.md`
  - documented that the historical short-bearing formulas are archival and that the current code integrates the long-bearing solution directly to get the net reaction vector.
