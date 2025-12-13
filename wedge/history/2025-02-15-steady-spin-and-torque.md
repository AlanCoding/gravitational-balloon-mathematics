# Steady Spin & Torque Integration — 2025‑02‑15

## Purpose

Add the angular-speed degree of freedom to each stage, replace the ad‑hoc linear velocity staging with the torque-balanced solution from `lit/torque.md`, and ensure both the steady-state setup and time-domain simulations use those speeds consistently. This eliminates the artificial transient created by mismatched torques and unlocks the torque equations needed for the angular momentum DOF.

## Key changes

1. **Steady spin solver (`wedge/steady_spin.py`)**
   - Implements the Couette torque coefficients per gap (`2π μ L R³ / c`) and a Gauss–Seidel solver (`steady_state_omegas`) that enforces equal torque through the stack for zero eccentricity.
   - Provides `signed_torque_on_inner` with the eccentricity factor `1/√(1−ε²)` from `lit/torque.md`, giving the fluid torque on each shell.
   - Includes a CLI (`python wedge/steady_spin.py`) that prints the steady angular speeds, surface speeds, and the uniform torque transmitted through all 16 gaps for debugging/validation.

2. **Geometry module updates (`wedge/positional_250.py`)**
   - Imports the solver to compute `TORQUE_COEFFS`, `SHELL_OMEGA_STEADY`, the corresponding surface speeds, and the baseline relative slips `U_rel`. These now replace the previous linear staging everywhere `positional_250` is imported, so the initial condition matches the torque-balanced state.

3. **Time-domain dynamics with ω DOFs (`wedge/multi_shell_time_sim.py`)**
   - State vector expanded to `(x, y, ω)` per moving shell; initial ω values pulled from `SHELL_OMEGA_STEADY`.
   - Each timestep recomputes relative slip from the current angular speeds, applies both force and torque balances per gap (using `signed_torque_on_inner`), and integrates angular acceleration via a thin-ring inertia estimate.
   - Progress logging and plotting now include angular-speed diagnostics, confirming that the steadystate spin profile holds (or evolves) during the coupled dynamics.

## Verification

* `python wedge/steady_spin.py` prints steady speeds and shows uniform torque across all gaps.
* `MPLBACKEND=Agg python wedge/multi_shell_time_sim.py` runs with the enlarged state and reports progress/plots without errors.
* The existing plotting scripts (`sim_250.py`, `time_sim_250.py`) still run, now drawing on the torque-balanced speeds.

This establishes the angular-momentum DOF groundwork; future work can focus on how orbital motion modifies the slip (ΔU) and on coupling structural torques or damping as needed.
