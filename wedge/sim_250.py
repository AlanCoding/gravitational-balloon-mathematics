import numpy as np
import matplotlib.pyplot as plt

# Parameters and force law from the laminar wedge model
from positional_250 import (
    N_SHELLS,
    C,
    MU,
    U_rel,
    L,
    R,
    SHELL_OMEGA_STEADY,
    TORQUE_COEFFS,
    total_fluid_forces,
    pressure_profile,
)
from steady_spin import signed_torque_on_inner

# -------------------------------------------------------
# Static "simulation": sweep hull offset and compute forces
# -------------------------------------------------------

def sweep_hull_offset(e_min=0.0, e_max_factor=0.95, n_points=200):
    """
    Vary the hull (shell 0) offset along +x from e_min to e_max_factor * C0,
    with all other shells fixed at the origin. Compute the fluid force on
    the hull for each offset.

    Returns:
        e_vals : offsets [m]
        Fx_hull: x-component of total pressure resultant on shell 0 [N]
        Fy_hull: y-component of total pressure resultant on shell 0 [N]
        Ftq    : torque divided by radius (force-equivalent) [N]
    """
    # Clearance for the innermost gap (between shell 0 and 1)
    C0 = C[0]

    # Offset range
    e_max = e_max_factor * C0
    e_vals = np.linspace(e_min, e_max, n_points)

    Fx_hull = np.zeros_like(e_vals)
    Fy_hull = np.zeros_like(e_vals)
    Ftq = np.zeros_like(e_vals)

    # Global dof count
    n_dofs = 2 * N_SHELLS
    omega_inner = SHELL_OMEGA_STEADY[0]
    omega_outer = SHELL_OMEGA_STEADY[1]
    torque_coeff = TORQUE_COEFFS[0]
    radius = R[0]

    for k, e in enumerate(e_vals):
        # Build configuration: all shells at origin except hull x = e
        q = np.zeros(n_dofs)
        q[0] = e  # shell 0, x-component

        F = total_fluid_forces(q, C, MU, U_rel, L)
        Fx_hull[k], Fy_hull[k] = F[0], F[1]

        torque = signed_torque_on_inner(
            omega_inner,
            omega_outer,
            torque_coeff,
            e,
            C0,
        )
        Ftq[k] = torque / radius

    return e_vals, Fx_hull, Fy_hull, Ftq


def main():
    # Run the sweep
    e_vals, Fx_hull, Fy_hull, Ftq = sweep_hull_offset(
        e_min=0.0,
        e_max_factor=0.95,  # up to 0.95 * C0
        n_points=300,
    )

    # For this setup (hull offset along +x, outer shells at origin),
    # Fx is radial, Fy is tangential.
    Fr = Fx_hull
    Ft = Fy_hull
    Fmag = np.sqrt(Fr**2 + Ft**2)
    force_angles = np.degrees(np.arctan2(Ft, Fr))

    # -----------------
    # Make the plots
    # -----------------

    # 1) Cartesian force components (pressure resultant) and torque-equivalent
    plt.figure()
    plt.plot(e_vals, Fr, label=r"$F_r$ (pressure resultant, x-comp)")
    plt.plot(e_vals, Ft, label=r"$F_t$ (pressure resultant, y-comp)")
    plt.plot(e_vals, Ftq, label=r"$T/R$ (torque ÷ radius)")
    plt.xlabel("Hull offset e [m]")
    plt.ylabel("Force on hull [N]")
    plt.title("Wedge forces on hull vs offset (gap 0, laminar model)")
    plt.legend()
    plt.grid(True)

    # 2) Ratio |Fr| / Ft vs offset (to see how radial stiffens faster)
    # Avoid divide-by-zero issues at e=0
    ratio = np.zeros_like(e_vals)
    mask = np.abs(Ft) > 0
    ratio[mask] = np.abs(Fr[mask]) / np.abs(Ft[mask])

    plt.figure()
    plt.plot(e_vals, ratio)
    plt.xlabel("Hull offset e [m]")
    plt.ylabel(r"$|F_r| / |F_t|$")
    plt.title("Radial vs tangential wedge strength")
    plt.grid(True)

    # 3) Resultant angle vs offset (attitude angle relative to +x)
    plt.figure()
    plt.plot(e_vals, force_angles)
    plt.xlabel("Hull offset e [m]")
    plt.ylabel("Resultant angle [deg]")
    plt.title("Pressure resultant angle vs offset")
    plt.grid(True)

    # 4) Sample pressure distributions
    sample_fracs = [0.1, 0.5, 0.8]
    theta_deg = None
    plt.figure()
    for frac in sample_fracs:
        e = frac * C[0]
        theta, pressure = pressure_profile(
            e,
            C[0],
            MU,
            U_rel[0],
            L,
            R[0],
        )
        if theta_deg is None:
            theta_deg = np.degrees(theta)
        plt.plot(theta_deg, pressure, label=f"e = {frac:.1f} c")
    plt.xlabel("θ [deg] (0 = max film thickness)")
    plt.ylabel("Pressure [Pa]")
    plt.title("Long-bearing pressure distributions for selected offsets")
    plt.legend()
    plt.grid(True)

    plt.show()


if __name__ == "__main__":
    main()
