# Controlled Offset Boundary — 2025‑02‑16

## Motivation

Following the idea in `CHANGEBLOG.md` that a deliberate x-offset might stabilize the wedge, this change introduces boundary conditions where the hull is held off-center by an external load, and each gap carries an equal radial reaction to balance it. This required a static offset solver plus plumbing in the time-domain sim so those new equilibria can be explored.

## Method

1. **Static radial load solver (`wedge/static_offset_solver.py`)**
   - Assumes all shells lie on the x-axis and that each gap operates in the zero-y plane (no twist).
   - With a prescribed hull x-offset (outer envelope fixed at 0), it seeks a common radial load `|F_r| = F*` so that each gap displacement produces that load. For a gap `i`, the magnitude `|F_r,i(e)|` is monotonically increasing up to cavitation, so a bisection in `e ∈ [0, 0.999c_i]` suffices to match any target load within feasible bounds.
   - A second bisection sweeps the shared load `F*` until the outermost shell lands at the desired position. This is effectively a 1‑D shooting method on the offsets.
   - The implementation assumes the direction is along +x, ignores tangential pressure components, and clips negative pressures as in the long-bearing radial solve. Given those simplifications, the solver produces a uniform `|F_r|` profile, but we should treat the result cautiously: any deviation from axisymmetry or tangential coupling could shift the true equilibrium, so this is best viewed as a first-order approximation.

2. **Simulation wiring (`wedge/multi_shell_time_sim.py`)**
   - Added CLI flags `--hull-offset` (meters) and `--initial-perturb` (meters). When the hull offset is non-zero, the static solver provides the baseline x-positions for all shells along with the per-gap load magnitude (logged for reference).
   - The global configuration `BASE_POSITIONS` now holds these offsets, and the state vector tracks deviations of shells 1…15 relative to that base. The RK4 loop still integrates `(x, y, ω)` for the moving shells, but every force/torque evaluation now uses the displaced base geometry.
   - The existing “bump shell 1 by 0.1 m” behavior is preserved via the `--initial-perturb` flag, so we can perturb the controlled-offset equilibrium before integrating.

3. **Demo/validation**
   - Running `python wedge/static_offset_solver.py 30` prints the offset ladder (shells 0→16 spanning ~30→0 m) and confirms each gap’s `|F_r|` matches the shared load (~82.8 N for the 30 m case).
   - `MPLBACKEND=Agg python wedge/multi_shell_time_sim.py --hull-offset 30 --initial-perturb 0.1` now starts from that equilibrium and logs its progress without numerical issues.

## Caveats

* The solver assumes each gap can be treated independently with scalar `e = |Δx|`, so any y-offset that develops later (as noted in `CHANGEBLOG.md`) is not captured in the initial state. Because the tangential force from the eccentric film is ignored in the static solve, the resulting equilibrium may drift in y once the time-domain dynamics start.
* The current solver only uses the radial component and the clipped Sommerfeld pressure, so if cavitation, tangential pressure, or structural springs are significant, we will need a coupled 2D solve instead of this 1D shooting approach.
* We still prescribe the hull offset directly; modeling the external actuator explicitly (springs/forces) would give more insight into how sensitive the system is to mis-specified loads.

Despite those limitations, the tooling now lets us explore the “intentional wedge preload” scenario mentioned in the changelog, and the CLI makes it easy to rerun parametrics (0–100 m offsets) to see how much axial clearance is consumed for a given control force. Future work should confirm the y-drift behavior and potentially augment the solver to balance both radial and tangential components.

## Accounting note: position array with/without offset

`N_SHELLS = 17`, so any global coordinate vector has `2 * N_SHELLS = 34` entries ordered `[x0, y0, x1, y1, …, x16, y16]`. We store these in `BASE_POSITIONS`, a `(17, 2)` array whose rows map directly to shells 0…16:

- Row 0 (columns 0/1) is the hull at `(x0, y0)`.
- Rows 1–15 are the moving friction-buffer shells.
- Row 16 is the outer stator, currently fixed at `(0, 0)`.

`deriv()` always begins by copying this array into `q_global = BASE_POSITIONS.reshape(-1).copy()`, so the full 34-element vector already contains the hull/stator coordinates before any dynamics are applied. In other words, we have **15 dynamic shells** (indices 1–15) whose positions are part of the state vector, plus **two fixed shells** (0 and 16) whose coordinates live in the array but never change.

### Zero-offset run

If `--hull-offset` is omitted (default 0), we leave `BASE_POSITIONS` filled with zeros:

```
BASE_POSITIONS =
[[0, 0],   # hull (shell 0)
 [0, 0],   # shell 1
 ...
 [0, 0]]   # stator (shell 16)
```

When we build `q_global`, it is just 34 zeros. We then loop over the moving shells (indices 1…15) and overwrite their slices with the dynamic state. The hull slice `q_global[0:2]` and stator slice `q_global[-2:]` are never touched again, so they remain at zero throughout the simulation—this is the “free concentric” boundary condition. Put differently: yes, there are 15 dynamic positions and 2 fixed ones, and without a hull offset the fixed entries are both zero.

### Non-zero hull offset

If `--hull-offset H` is supplied, we call `solve_static_offsets(H, outer_offset=0)`. That returns a 17-element vector of x offsets (y remains zero), for example:

```
[H, 28.01, 26.04, …, 1.76, ~0]
```

We write this into `BASE_POSITIONS[:, 0]`, so now:

```
BASE_POSITIONS =
[[H,      0],
 [28.01,  0],
 ...
 [~0,     0]]
```

`q_global` then starts with those values, and as before we overwrite only the rows for shells 1–15 with their dynamic deviations. Because rows 0 and 16 are never rewritten, the hull stays pinned at `x0 = H` and the stator at `x16 = 0` for the entire run—the “external force” is represented by holding those two entries fixed. The solver also reports the shared `|F_r|`, which is the fluid load that must balance whatever actuator is enforcing that hull offset. The “initial conditions” for the other 15 shells come from the same static solve (rather than a naive guess) so that every gap starts with equal radial load before the extra perturbation on shell 1 is applied.
