import sys
import time
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
import yaml

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
    set_radial_fudge_factor,
)
from static_offset_solver import solve_static_offsets
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

BASE_POSITIONS = np.zeros((N_SHELLS, 2))

DEFAULTS_DIR = Path(__file__).resolve().parent / "defaults"
DEFAULT_CONFIG = DEFAULTS_DIR / "multi_shell_time_sim.yaml"
RUN_INPUT_NAMES = ("inputs.yaml", "inputs.yml")


def _read_yaml(path):
    with path.open("r", encoding="utf-8") as stream:
        data = yaml.safe_load(stream)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValueError(f"YAML file {path} must define a dictionary.")
    return data


def _deep_merge(base, overrides):
    result = dict(base)
    for key, value in overrides.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_configuration(run_dir):
    config = {}
    if DEFAULT_CONFIG.exists():
        config = _read_yaml(DEFAULT_CONFIG)

    input_file = None
    for name in RUN_INPUT_NAMES:
        candidate = run_dir / name
        if candidate.exists():
            input_file = candidate
            break

    if input_file is None:
        available = ", ".join(RUN_INPUT_NAMES)
        raise FileNotFoundError(
            f"No input file found in {run_dir}. Expected one of: {available}"
        )

    run_config = _read_yaml(input_file)
    return _deep_merge(config, run_config)


def next_available_path(directory, desired_name):
    directory.mkdir(parents=True, exist_ok=True)
    base_path = directory / desired_name
    if not base_path.exists():
        return base_path

    stem = base_path.stem
    suffix = base_path.suffix
    counter = 1
    while True:
        candidate = directory / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


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
    q_global = BASE_POSITIONS.reshape(-1).copy()
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
    global C_DAMP
    if len(sys.argv) != 2:
        run_script = Path(__file__).name
        print(f"Usage: python {run_script} RUN_DIRECTORY", file=sys.stderr)
        sys.exit(1)

    run_dir = Path(sys.argv[1]).expanduser().resolve()
    if not run_dir.is_dir():
        raise FileNotFoundError(f"Run directory {run_dir} does not exist.")

    config = load_configuration(run_dir)
    sim_cfg = config.get("simulation", {})

    hull_offset = float(sim_cfg.get("hull_offset", 0.0))
    outer_offset = float(sim_cfg.get("outer_offset", 0.0))
    initial_perturb = float(sim_cfg.get("initial_perturb", 0.1))
    dt = float(sim_cfg.get("dt", 0.05))
    total_time = float(sim_cfg.get("total_time", 1000.0))
    print_interval = float(sim_cfg.get("print_interval", 2.0))
    damping = float(sim_cfg.get("damping", C_DAMP))
    track_shells = sim_cfg.get("track_shells", [1, 5, 10, 15])
    track_shells = [int(s) for s in track_shells if 1 <= s <= N_SHELLS - 2]
    forces_cfg = config.get("forces", {})
    fr_fudge = float(forces_cfg.get("radial_fudge", 1.0))

    if dt <= 0.0:
        raise ValueError("simulation.dt must be positive.")
    if total_time <= 0.0:
        raise ValueError("simulation.total_time must be positive.")

    C_DAMP = damping
    set_radial_fudge_factor(fr_fudge)

    base_positions = np.zeros((N_SHELLS, 2))
    base_positions[-1, 0] = outer_offset
    base_positions[0, 0] = hull_offset
    base_force = 0.0
    if abs(hull_offset) > 0.0 or abs(outer_offset) > 0.0:
        result = solve_static_offsets(
            hull_offset=hull_offset,
            outer_offset=outer_offset,
        )
        base_positions[:, 0] = result.offsets
        base_force = result.target_force
        print(f"[steady-offset] gap |Fr| = {base_force:.6e} N")

    BASE_POSITIONS[:] = base_positions

    pos0 = base_positions[moving_indices].copy()
    if n_move > 0:
        pos0[0, 0] += initial_perturb

    vel0 = np.zeros((n_move, 2))
    omega0 = SHELL_OMEGA_STEADY[moving_indices]

    state = np.concatenate([pos0.reshape(-1), vel0.reshape(-1), omega0])

    n_steps = max(1, int(np.ceil(total_time / dt)))
    times = np.zeros(n_steps + 1)

    track_idx = [moving_indices.index(s) for s in track_shells]
    xs = {s: np.zeros(n_steps + 1) for s in track_shells}
    ys = {s: np.zeros(n_steps + 1) for s in track_shells}
    omegas = {s: np.zeros(n_steps + 1) for s in track_shells}

    for s, j in zip(track_shells, track_idx):
        xs[s][0] = pos0[j, 0]
        ys[s][0] = pos0[j, 1]
        omegas[s][0] = omega0[j]

    t = 0.0
    n_last = 0
    next_print = (
        time.perf_counter() + print_interval if print_interval > 0.0 else None
    )

    try:
        for n in range(1, n_steps + 1):
            state = rk4_step(state, dt)
            t += dt

            times[n] = t
            n_last = n

            pos = state[:2*n_move].reshape((n_move, 2))
            vel = state[2*n_move:4*n_move].reshape((n_move, 2))
            omega = state[4*n_move:]

            for s, j in zip(track_shells, track_idx):
                xs[s][n] = pos[j, 0]
                ys[s][n] = pos[j, 1]
                omegas[s][n] = omega[j]

            if next_print is not None:
                now = time.perf_counter()
                if now < next_print:
                    continue
                max_disp = np.max(np.linalg.norm(pos, axis=1)) if pos.size else 0.0
                avg_speed = np.mean(np.linalg.norm(vel, axis=1)) if n_move else 0.0
                avg_omega = np.mean(omega) if omega.size else 0.0
                print(
                    f"[progress] sim t = {t:9.1f}s / {total_time:9.1f}s "
                    f"({100 * t / total_time:5.1f}%)  |  "
                    f"max|pos| = {max_disp:7.3f} m, avg|vel| = {avg_speed:7.3f} m/s, "
                    f"avg ω = {avg_omega:7.4f} rad/s"
                )
                next_print = now + print_interval

    except ValueError as exc:
        print(f"\nSimulation aborted at step {n_last}, t ≈ {times[n_last]:.3f} s")
        print(f"Reason: {exc}")

    times_plot = times[:n_last+1]
    xs_plot = {s: arr[:n_last+1] for s, arr in xs.items()}
    ys_plot = {s: arr[:n_last+1] for s, arr in ys.items()}
    omega_plot = {s: arr[:n_last+1] for s, arr in omegas.items()}

    plot_cfg = config.get("output", {}).get("plots", {})
    filename_x = plot_cfg.get("x_time", "x_time.png")
    filename_y = plot_cfg.get("y_time", "y_time.png")
    filename_xy = plot_cfg.get("xy", "trajectories.png")
    filename_omega = plot_cfg.get("omega", "omega.png")

    if track_shells:
        fig = plt.figure()
        for s in track_shells:
            plt.plot(times_plot, xs_plot[s], label=f"shell {s} x(t)")
        plt.xlabel("Time [s]")
        plt.ylabel("x displacement [m]")
        plt.title("Friction-buffer x(t) trajectories")
        plt.legend()
        plt.grid(True)
        save_path = next_available_path(run_dir, filename_x)
        fig.savefig(save_path)
        plt.close(fig)
        print(f"[output] saved {save_path}")

        fig = plt.figure()
        for s in track_shells:
            plt.plot(times_plot, ys_plot[s], label=f"shell {s} y(t)")
        plt.xlabel("Time [s]")
        plt.ylabel("y displacement [m]")
        plt.title("Friction-buffer y(t) trajectories")
        plt.legend()
        plt.grid(True)
        save_path = next_available_path(run_dir, filename_y)
        fig.savefig(save_path)
        plt.close(fig)
        print(f"[output] saved {save_path}")

        fig = plt.figure()
        for s in track_shells:
            plt.plot(xs_plot[s], ys_plot[s], label=f"shell {s}")
        plt.xlabel("x [m]")
        plt.ylabel("y [m]")
        plt.axis("equal")
        plt.title("Friction-buffer trajectories in cross-section")
        plt.legend()
        plt.grid(True)
        save_path = next_available_path(run_dir, filename_xy)
        fig.savefig(save_path)
        plt.close(fig)
        print(f"[output] saved {save_path}")

        fig = plt.figure()
        for s in track_shells:
            plt.plot(times_plot, omega_plot[s], label=f"shell {s} ω(t)")
        plt.xlabel("Time [s]")
        plt.ylabel("Angular speed [rad/s]")
        plt.title("Shell angular speeds vs time")
        plt.legend()
        plt.grid(True)
        save_path = next_available_path(run_dir, filename_omega)
        fig.savefig(save_path)
        plt.close(fig)
        print(f"[output] saved {save_path}")
    else:
        print("[output] No track shells specified; skipping plots.")


if __name__ == "__main__":
    main()
