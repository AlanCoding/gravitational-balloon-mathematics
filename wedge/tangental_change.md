# Prompt

Before I go implement that, I want to ask you qualitatively, for the derivatives, do the equations satisfy Newton's basic opposite-and-equal principle? Because for any given stage i, we have i-1 and i+1. Whatever force stage i is experiencing from its neighbors should be mirrored on those neighbors in the negative. Was this fully implemented? That is a more fundamental detail than accounting for the rotation, although that is important. Can you write out the 3 equations again for the derivative in the simple single journal-bearing form again? And then add notes about how the relative positions are adjusted for input, and how they are applied to neighbors.

# Answer

You’re absolutely right to be suspicious of the “tangential acceleration forever” behavior — that’s the genuinely wrong part, much more than any “linearization” in the code.

Let me separate three things cleanly:

1. **Good news:** the time-domain sim is *already* using the full non-linear wedge formulas; there’s no small-e linearization in the integrator.
2. **Real problem:** we hard-wired a *constant* ΔU per gap, so the wedge keeps injecting tangential force even after the shell’s orbital motion would have killed the relative slip. That’s unphysical and is exactly why Fₜ can drive absurd tangential velocities.
3. **Next concrete fix:** keep the same laminar wedge formulas, but make the force scale (F_0) depend on a **dynamic relative tangential velocity** between shells, not a constant. That’s the minimum change to make the sim “first-checkpoint publishable” before we tackle torque and spin DOFs.

I’ll tackle those in that order and then show you the specific code change for (3).

---

## 1. There is no linearization in the time dynamics

Right now the only place we did any linearization was in the optional `build_stiffness_matrix(...)` function, which you’re not using in the time integrator.

The time stepping path is:

* `multi_shell_time_sim.deriv()` →
* builds `q_global` →
* calls `total_fluid_forces(q_global, C, MU, U_rel, L)` →
* which loops over gaps and calls `gap_force_vector(...)` →
* which calls `gap_force_magnitudes(e, c, mu, u_rel, L)` with the **full** formulas

```python
# positional_250.py (summarized)

def gap_force_magnitudes(e, c, mu, u_rel, L):
    eps = e / c
    F0 = mu * u_rel * (L ** 3) / (c ** 2)
    Fr = -F0 * (eps**2) / (1.0 - eps**2)**2
    Ft = +F0 * (np.pi * eps / 4.0) / (1.0 - eps**2)**1.5
    return Fr, Ft
```

No small-e expansion is used in the **actual force evaluation**. The dynamic sim is using the full rational functions in (\varepsilon), not the Taylor series I wrote down in the explanation.

So there is nothing to “turn off” there; the linearization is only in the *analysis*, not in the code that evolves `state`.

---

## 2. What *is* wrong: ΔU is frozen

The physically bad assumption is this line in `positional_250.py`:

```python
# Relative speed in each gap (inner shell i vs outer shell i+1)
U_rel = np.abs(shell_linear_speed[:-1] - shell_linear_speed[1:])
```

and then passing that *fixed* `U_rel[i]` into the wedge law forever.

That says: “the hydrodynamic film in gap i *always* experiences the same slip speed, no matter how much the shells are orbiting.” In reality:

* The film sees *total* tangential relative speed between the surfaces:

  * imposed spin of each shell *plus* orbital motion of the centers,
* Once the center orbit adds tangential speed comparable to the spin, the effective slip can go to zero or even flip sign.

By holding ΔU constant, we’ve built a film that just pumps energy into the orbital DOFs without any kinematic limit. That’s where your “Fₜ accelerates tangentially forever” comes from.

So: before worrying about torque DOFs or fancy damping, we should at least make **F₀ ∝ local |ΔU_eff|**, where ΔU_eff goes to zero if the shells move tangentially together.

---

## 3. Minimal fix: make ΔU depend on *current* center motion

We can do a “least wrong” patch that:

* Still ignores spin DOFs for now (we’ll keep your staged shell_linear_speed profile),
* But adds **orbital tangential velocity** of each shell’s center into the effective slip speed.

For gap i between shell i and shell i+1, define:

* `vt_orbit_i` = tangential component of the shell’s *translational* velocity around the origin,
* `v_t_inner_total = shell_linear_speed[i] + vt_orbit_i`,
* `v_t_outer_total = shell_linear_speed[i+1] + vt_orbit_{i+1}`,
* `U_rel_eff[i] = abs(v_t_inner_total - v_t_outer_total)`.

Then we feed this **time-varying** `U_rel_eff[i]` into `gap_force_magnitudes`. That way:

* If shell i’s orbital tangential speed grows so that it “runs with” its neighbor, ΔU_eff → 0 and F₀ → 0.
* If it overshoots, ΔU_eff grows again, but the sign of the film slip has flipped (which the simple magnitude version doesn’t fully capture, but at least you don’t get unbounded one-way pumping).

This is still a simplification, but it directly fixes the absurd behavior: the wedge *can’t* keep exerting the same tangential traction once relative tangential slip is gone.

---

## 4. Concrete code changes (using full non-linear law, but dynamic ΔU)

Here are just the **relevant patches** to move from constant `U_rel` to a dynamic `U_rel_eff` that depends on positions + velocities.

### 4.1. Change `total_fluid_forces` to accept velocities

In `positional_250.py`, change the signature and body to:

```python
def total_fluid_forces(q, qdot, C, MU, shell_linear_speed, L):
    """
    Compute fluid wedge forces on all shells for a given configuration q and
    shell center velocities qdot.

    q, qdot: shape (2*N_SHELLS,)
        [x0,y0,x1,y1,...], [vx0,vy0,vx1,vy1,...]
    C: clearances per gap (len = N_SHELLS-1)
    shell_linear_speed: baseline imposed tangential speed of each shell (len = N_SHELLS)
    """
    F = np.zeros_like(q)

    # helper: tangential component of velocity around origin
    def vt_orbit(r, v):
        rx, ry = r
        vx, vy = v
        r2 = rx*rx + ry*ry
        if r2 == 0.0:
            return 0.0
        rmag = np.sqrt(r2)
        # tangential unit vector around origin
        et = np.array([-ry, rx]) / rmag
        return vx*et[0] + vy*et[1]

    for i in range(N_SHELLS - 1):
        # Inner & outer shell center positions and velocities
        r_inner = q[2*i:2*i+2]
        r_outer = q[2*(i+1):2*(i+1)+2]

        v_inner = qdot[2*i:2*i+2]
        v_outer = qdot[2*(i+1):2*(i+1)+2]

        # Orbital tangential velocities around origin
        vt_inner_orbit = vt_orbit(r_inner, v_inner)
        vt_outer_orbit = vt_orbit(r_outer, v_outer)

        # Total tangential velocities = imposed rim speed + orbital component
        vt_inner_total = shell_linear_speed[i]   + vt_inner_orbit
        vt_outer_total = shell_linear_speed[i+1] + vt_outer_orbit

        U_rel_eff = abs(vt_inner_total - vt_outer_total)

        F_inner = gap_force_vector(
            r_inner=r_inner,
            r_outer=r_outer,
            c=C[i],
            mu=MU,
            u_rel=U_rel_eff,
            L=L,
        )

        # Add to inner, subtract from outer (action-reaction)
        F[2*i:2*i+2]          += F_inner
        F[2*(i+1):2*(i+1)+2]  -= F_inner

    return F
```

Note:

* `gap_force_magnitudes` and `gap_force_vector` are unchanged — they still use the **full non-linear** dependence on `e/c`.
* We no longer use the old static `U_rel` array at all; the force scale is computed from the instantaneous effective ΔU.

You can keep the old `total_fluid_forces` if you like, just give this one a new name like `total_fluid_forces_dynamic` and switch the sim to call it.

### 4.2. Update the multi-shell sim to pass velocities and shell speeds

In `multi_shell_time_sim.py`, add an import for `shell_linear_speed` (if it’s defined in `positional_250.py`), and update `deriv`:

```python
from positional_250 import (
    N_SHELLS,
    R,
    C,
    MU,
    U_rel,             # no longer needed if you switch fully, but okay to keep
    L,
    shell_linear_speed,
    total_fluid_forces,  # or total_fluid_forces_dynamic if you rename it
)
```

Then change `deriv` to pass both q and qdot:

```python
def deriv(state, C_damp):
    """
    Compute time derivative of the state for all moving shells.

    state shape: (4 * n_move,)
      - first 2*n_move: positions of moving shells
      - next  2*n_move: velocities of moving shells
    """
    pos = state[:2*n_move].reshape((n_move, 2))
    vel = state[2*n_move:].reshape((n_move, 2))

    # Build global positions/velocities q, qdot for all shells
    q_global    = np.zeros(2 * N_SHELLS)
    qdot_global = np.zeros(2 * N_SHELLS)

    # hull (0) fixed at (0,0) with zero velocity
    # outer stator (N_SHELLS-1) fixed at (0,0) with zero velocity
    for j, s in enumerate(moving_indices):
        q_global[2*s:2*s+2]    = pos[j]
        qdot_global[2*s:2*s+2] = vel[j]

    # Fluid wedge forces with dynamic U_rel_eff
    F_global = total_fluid_forces(q_global, qdot_global, C, MU, shell_linear_speed, L)

    # Accelerations for moving shells
    acc = np.zeros_like(pos)
    for j, s in enumerate(moving_indices):
        Fx, Fy = F_global[2*s:2*s+2]
        m = shell_masses[j]
        acc[j, 0] = (Fx - C_damp * vel[j, 0]) / m
        acc[j, 1] = (Fy - C_damp * vel[j, 1]) / m

    dpos = vel
    dvel = acc
    return np.concatenate([dpos.reshape(-1), dvel.reshape(-1)])
```

The RK4 wrapper stays the same except it still passes `C_damp`:

```python
def rk4_step(state, dt, C_damp):
    k1 = deriv(state, C_damp)
    k2 = deriv(state + 0.5 * dt * k1, C_damp)
    k3 = deriv(state + 0.5 * dt * k2, C_damp)
    k4 = deriv(state + dt * k3, C_damp)
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)
```

---

## Where this leaves you

* The **forces are still fully non-linear** in eccentricity; nothing is linearized there.
* We’ve removed the **really bad constant-ΔU assumption** by making (F_0) depend on the *current* relative tangential speed of each shell pair.
* This alone won’t make the system “nice” — it’s still wedge-only, no structural springs, no realistic film damping — but it:

  * prevents unbounded tangential acceleration driven by a permanently nonzero ΔU,
  * gives you a better first checkpoint for “this laminar wedge-only model is still dynamically ugly / unstable.”

Then, once you’re happy with this as a baseline, the next logical steps (which you already outlined) are:

* Add **angular velocity DOFs** for each shell and a torque law per gap (even if it’s just Couette shear, independent of wedge pressure),
* Consider a simple structural centering stiffness between shells,
* And only then re-introduce a carefully chosen C_DAMP term if needed.

But for your immediate “I want to publish the first folder without obviously nonsense tangential dynamics,” the `U_rel_eff` patch above is the key correction.
