import numpy as np
import matplotlib.pyplot as plt

# Import parameters and functions from your existing file
from positional_250 import (
    N_SHELLS,
    C,
    MU,
    U_rel,
    L,
    total_fluid_forces,
)


# ---------------------------
# Dynamic parameters (tunable)
# ---------------------------

# Effective mass of hull (per axial length, or just "mass" in this 2D model)
M_HULL = 1.0e8      # kg, arbitrary but big; tweak as needed

# Structural centering stiffness and damping
K_CENTER = 1.0e6    # N/m, isotropic
C_DAMP   = 0.0    # N·s/m, isotropic
# C_DAMP values with the old short-journal assumption
# 1.0e5 made the 5th stage go unstable before the 1st

# Time integration
DT      = 0.1       # s
T_FINAL = 2.0e4     # s
N_STEPS = int(T_FINAL / DT)


# ---------------------------
# Force on the hull (only)
# ---------------------------

def hull_force(x, y, vx, vy):
    """
    Compute total force on the hull (shell 0) at given position/velocity.

    Uses:
      - Wedge fluid force from total_fluid_forces
      - Linear centering spring force
      - Linear viscous damping
    """
    # Build global configuration q: hull at (x,y), others fixed at (0,0)
    q = np.zeros(2 * N_SHELLS)
    q[0] = x
    q[1] = y

    F_all = total_fluid_forces(q, C, MU, U_rel, L)
    Fx_fluid, Fy_fluid = F_all[0], F_all[1]

    # Structural centering force (spring to origin)
    Fx_spring = -K_CENTER * x
    Fy_spring = -K_CENTER * y

    # Damping
    Fx_damp = -C_DAMP * vx
    Fy_damp = -C_DAMP * vy

    Fx = Fx_fluid + Fx_spring + Fx_damp
    Fy = Fy_fluid + Fy_spring + Fy_damp
    return Fx, Fy


# ---------------------------
# RK4 integrator for hull motion
# ---------------------------

def deriv(state):
    """
    Compute time derivative of state = [x, y, vx, vy].
    """
    x, y, vx, vy = state
    Fx, Fy = hull_force(x, y, vx, vy)

    ax = Fx / M_HULL
    ay = Fy / M_HULL

    return np.array([vx, vy, ax, ay])


def rk4_step(state, dt):
    """
    One RK4 step for the 2D hull dynamics.
    """
    k1 = deriv(state)
    k2 = deriv(state + 0.5 * dt * k1)
    k3 = deriv(state + 0.5 * dt * k2)
    k4 = deriv(state + dt * k3)
    return state + (dt / 6.0) * (k1 + 2*k2 + 2*k3 + k4)


# ---------------------------
# Main simulation
# ---------------------------

def main():
    # Initial condition: small offset, zero velocity
    x0 = 0.1   # m
    y0 = 0.0   # m
    vx0 = 0.0  # m/s
    vy0 = 0.0  # m/s

    state = np.array([x0, y0, vx0, vy0])

    # Storage
    times = np.zeros(N_STEPS + 1)
    xs    = np.zeros(N_STEPS + 1)
    ys    = np.zeros(N_STEPS + 1)
    vxs   = np.zeros(N_STEPS + 1)
    vys   = np.zeros(N_STEPS + 1)

    xs[0], ys[0], vxs[0], vys[0] = state
    t = 0.0

    for n in range(1, N_STEPS + 1):
        state = rk4_step(state, DT)
        t += DT

        times[n] = t
        xs[n], ys[n], vxs[n], vys[n] = state

    # -----------------
    # Plots
    # -----------------

    # 1) x(t) and y(t)
    plt.figure()
    plt.plot(times, xs, label="x(t)")
    plt.plot(times, ys, label="y(t)")
    plt.xlabel("Time [s]")
    plt.ylabel("Displacement [m]")
    plt.title("Hull displacement vs time")
    plt.legend()
    plt.grid(True)

    # 2) Phase portrait (orbit in x–y)
    plt.figure()
    plt.plot(xs, ys)
    plt.xlabel("x [m]")
    plt.ylabel("y [m]")
    plt.title("Hull trajectory in the cross-section plane")
    plt.axis("equal")
    plt.grid(True)

    # 3) Speed vs time (optional)
    speed = np.sqrt(vxs**2 + vys**2)
    plt.figure()
    plt.plot(times, speed)
    plt.xlabel("Time [s]")
    plt.ylabel("Speed [m/s]")
    plt.title("Hull translational speed vs time")
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()

