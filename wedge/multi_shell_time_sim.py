import time
import numpy as np
import matplotlib.pyplot as plt

# Import your laminar wedge model & geometry
from positional_250 import (
    N_SHELLS,
    R,          # radii of shells (inner radius of each shell)
    C,          # clearances per gap (len = N_SHELLS-1)
    MU,
    L,          # axial length
    TORQUE_COEFFS,
    SHELL_OMEGA_STEADY,
    total_fluid_forces,
)
from steady_spin import signed_torque_on_inner

# ----------------------------------------------------
# Mass model: each friction-buffer shell gets a mass
# ≈ 1/4 of the air mass in its inner annulus
# ----------------------------------------------------

rho_air = 1.2  # kg/m^3

# Air mass in each annulus (gap between shell i and i+1)
gap_masses = np.zeros(N_SHELLS - 1)
for i in range(N_SHELLS - 1):
    R_inner = R[i]
    R_outer = R[i+1]
    volume = np.pi * (R_outer**2 - R_inner**2) * L   # exact annulus volume
    gap_masses[i] = rho_air * volume

# Moving shells: 1..N_SHELLS-2 (hull 0 fixed, outer stator N_SHELLS-1 fixed)
moving_indices = list(range(1, N_SHELLS - 1))
n_move = len(moving_indices)

# Assign each moving shell a mass = 1/4 of the air mass in its *inner* annulus
shell_masses = np.zeros(n_move)
for j, s in enumerate(moving_indices):
    shell_masses[j] = 0.25 * gap_masses[s - 1]

# Small isotropic damping for each shell (to keep things from ringing forever)
C_DAMP = 3e4  # N·s/m; set >0 if you want some damping

# Rotational inertia per moving shell (approximate thin ring: I = m * R^2)
shell_inertias = np.zeros(n_move)
for j, s in enumerate(moving_indices):
    shell_inertias[j] = shell_masses[j] * (R[s] ** 2)


# ----------------------------------------------------
# Dynamics: state = [positions(2*n_move), velocities(2*n_move), omegas(n_move)]
# ----------------------------------------------------

def deriv(state):
    """
    Compute time derivative of the state for all moving shells.

    state shape: (5 * n_move,)
      - first 2*n_move entries: [x_1, y_1, x_2, y_2, ..., x_{N-2}, y_{N-2}]
      - next  2*n_move entries: [vx_1, vy_1, vx_2, vy_2, ..., vx_{N-2}, vy_{N-2}]
      - final n_move entries: angular velocities ω_s for moving shells
    """
    pos = state[:2*n_move].reshape((n_move, 2))
    vel = state[2*n_move:4*n_move].reshape((n_move, 2))
    omega = state[4*n_move:]

    # Build global positions + angular speeds for all shells
    q_global = np.zeros(2 * N_SHELLS)
    omega_global = np.array(SHELL_OMEGA_STEADY, copy=True)
    for j, s in enumerate(moving_indices):
        q_global[2*s:2*s+2] = pos[j]
        omega_global[s] = omega[j]

    # Relative tangential slip from current angular speeds
    u_rel = np.abs(omega_global[:-1] * R[:-1] - omega_global[1:] * R[1:])

    # Fluid wedge forces on all shells
    F_global = total_fluid_forces(q_global, C, MU, u_rel, L)

    # Fluid torques on each shell (array length N_SHELLS)
    T_global = np.zeros(N_SHELLS)
    for i in range(N_SHELLS - 1):
        r_inner = q_global[2*i:2*i+2]
        r_outer = q_global[2*(i+1):2*(i+1)+2]
        e = np.linalg.norm(r_inner - r_outer)
        torque_inner = signed_torque_on_inner(
            omega_global[i],
            omega_global[i+1],
            TORQUE_COEFFS[i],
            e,
            C[i],
        )
        T_global[i] += torque_inner
        T_global[i+1] -= torque_inner

    # Accelerations for moving shells
    acc = np.zeros_like(pos)
    for j, s in enumerate(moving_indices):
        Fx, Fy = F_global[2*s:2*s+2]
        m = shell_masses[j]
        acc[j, 0] = (Fx - C_DAMP * vel[j, 0]) / m
        acc[j, 1] = (Fy - C_DAMP * vel[j, 1]) / m

    # Angular accelerations
    alpha = np.zeros_like(omega)
    for j, s in enumerate(moving_indices):
        torque = T_global[s]
        I = shell_inertias[j]
        if I > 0.0:
            alpha[j] = torque / I

    dpos = vel
    dvel = acc
    domega = alpha

    return np.concatenate([dpos.reshape(-1), dvel.reshape(-1), domega])


def rk4_step(state, dt):
    k1 = deriv(state)
    k2 = deriv(state + 0.5 * dt * k1)
    k3 = deriv(state + 0.5 * dt * k2)
    k4 = deriv(state + dt * k3)
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)


# ----------------------------------------------------
# Time simulation
# ----------------------------------------------------

def main():
    # Initial conditions:
    # - Start with all shells concentric,
    #   except give the first friction buffer (shell 1) a small x-offset.
    pos0 = np.zeros((n_move, 2))
    pos0[0, 0] = 0.1  # shell 1 offset 0.1 m in +x

    vel0 = np.zeros((n_move, 2))
    omega0 = SHELL_OMEGA_STEADY[moving_indices]

    state = np.concatenate([pos0.reshape(-1), vel0.reshape(-1), omega0])

    # Time integration parameters
    DT = 0.05        # s, timestep
    T_FINAL = 10000  # s, total simulation time
    N_STEPS = int(T_FINAL / DT)

    times = np.zeros(N_STEPS + 1)
    # Store positions for a subset of shells to avoid too much clutter
    track_shells = [1, 5, 10, 15]  # shell indices to monitor (if exist)
    track_shells = [s for s in track_shells if 1 <= s <= N_SHELLS - 2]

    # Map these to moving-shell indices
    track_idx = [moving_indices.index(s) for s in track_shells]

    xs = {s: np.zeros(N_STEPS + 1) for s in track_shells}
    ys = {s: np.zeros(N_STEPS + 1) for s in track_shells}
    omegas = {s: np.zeros(N_STEPS + 1) for s in track_shells}

    # Record initial positions
    for s, j in zip(track_shells, track_idx):
        xs[s][0] = pos0[j, 0]
        ys[s][0] = pos0[j, 1]
        omegas[s][0] = omega0[j]

    t = 0.0
    n_last = 0  # last valid index

    print_interval = 2.0  # seconds of wall time
    next_print = time.perf_counter() + print_interval

    try:
        for n in range(1, N_STEPS + 1):
            # One RK4 step; this is where we can hit e >= C and raise ValueError
            state = rk4_step(state, DT)
            t += DT

            times[n] = t
            n_last = n

            pos = state[:2*n_move].reshape((n_move, 2))
            vel = state[2*n_move:4*n_move].reshape((n_move, 2))
            omega = state[4*n_move:]

            for s, j in zip(track_shells, track_idx):
                xs[s][n] = pos[j, 0]
                ys[s][n] = pos[j, 1]
                omegas[s][n] = omega[j]

            now = time.perf_counter()
            if now >= next_print:
                max_disp = np.max(np.linalg.norm(pos, axis=1)) if pos.size else 0.0
                avg_speed = np.mean(np.linalg.norm(vel, axis=1)) if n_move else 0.0
                avg_omega = np.mean(omega) if omega.size else 0.0
                print(
                    f"[progress] sim t = {t:9.1f}s / {T_FINAL:9.1f}s "
                    f"({100 * t / T_FINAL:5.1f}%)  |  "
                    f"max|pos| = {max_disp:7.3f} m, avg|vel| = {avg_speed:7.3f} m/s, "
                    f"avg ω = {avg_omega:7.4f} rad/s"
                )
                next_print = now + print_interval

    except ValueError as exc:
        # We hit the "offset e >= clearance c" condition somewhere in the RK4 stages
        print(f"\nSimulation aborted at step {n_last}, t ≈ {times[n_last]:.3f} s")
        print(f"Reason: {exc}")

    # Trim arrays to the last valid index so plots don't include uninitialized tail
    times_plot = times[:n_last+1]
    xs_plot = {s: arr[:n_last+1] for s, arr in xs.items()}
    ys_plot = {s: arr[:n_last+1] for s, arr in ys.items()}
    omega_plot = {s: arr[:n_last+1] for s, arr in omegas.items()}

    # -----------------
    # Plots
    # -----------------

    # 1) x(t) for selected shells
    plt.figure()
    for s in track_shells:
        plt.plot(times_plot, xs_plot[s], label=f"shell {s} x(t)")
    plt.xlabel("Time [s]")
    plt.ylabel("x displacement [m]")
    plt.title("Friction-buffer x(t) trajectories")
    plt.legend()
    plt.grid(True)

    # 2) y(t) for selected shells
    plt.figure()
    for s in track_shells:
        plt.plot(times_plot, ys_plot[s], label=f"shell {s} y(t)")
    plt.xlabel("Time [s]")
    plt.ylabel("y displacement [m]")
    plt.title("Friction-buffer y(t) trajectories")
    plt.legend()
    plt.grid(True)

    # 3) Orbits in x–y for selected shells
    plt.figure()
    for s in track_shells:
        plt.plot(xs_plot[s], ys_plot[s], label=f"shell {s}")
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.axis("equal")
    plt.title("Friction-buffer trajectories in cross-section")
    plt.legend()
    plt.grid(True)

    # 4) Angular speed evolution
    plt.figure()
    for s in track_shells:
        plt.plot(times_plot, omega_plot[s], label=f"shell {s} ω(t)")
    plt.xlabel("Time [s]")
    plt.ylabel("Angular speed [rad/s]")
    plt.title("Shell angular speeds vs time")
    plt.legend()
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()
