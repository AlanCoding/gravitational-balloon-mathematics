import numpy as np
import matplotlib.pyplot as plt

# Import parameters and functions from your existing script
from positional_250 import (
    N_SHELLS,
    C,
    MU,
    U_rel,
    L,
    total_fluid_forces,
)

# -------------------------------------------------------
# Static "simulation": sweep hull offset and compute forces
# -------------------------------------------------------

def sweep_hull_offset(e_min=0.0, e_max_factor=0.95, n_points=200):
    """
    Vary the hull (shell 0) offset along +x from e_min to e_max_factor * C0,
    with all other shells fixed at the origin. Compute the fluid force on
    the hull for each offset.

    Returns:
        e_vals : array of offsets [m]
        Fx_hull: fluid force x-component [N]
        Fy_hull: fluid force y-component [N]
    """
    # Clearance for the innermost gap (between shell 0 and 1)
    C0 = C[0]

    # Offset range
    e_max = e_max_factor * C0
    e_vals = np.linspace(e_min, e_max, n_points)

    Fx_hull = np.zeros_like(e_vals)
    Fy_hull = np.zeros_like(e_vals)

    # Global dof count
    n_dofs = 2 * N_SHELLS

    for k, e in enumerate(e_vals):
        # Build configuration: all shells at origin except hull x = e
        q = np.zeros(n_dofs)
        q[0] = e  # shell 0, x-component

        F = total_fluid_forces(q, C, MU, U_rel, L)
        Fx_hull[k], Fy_hull[k] = F[0], F[1]

    return e_vals, Fx_hull, Fy_hull


def main():
    # Run the sweep
    e_vals, Fx_hull, Fy_hull = sweep_hull_offset(
        e_min=0.0,
        e_max_factor=0.95,  # up to 0.95 * C0
        n_points=300,
    )

    # For this setup (hull offset along +x, outer shells at origin),
    # Fx is radial, Fy is tangential.
    Fr = Fx_hull
    Ft = Fy_hull
    Fmag = np.sqrt(Fr**2 + Ft**2)

    # -----------------
    # Make the plots
    # -----------------

    # 1) Radial and tangential forces vs offset
    plt.figure()
    plt.plot(e_vals, Fr, label=r"$F_r$ (radial, x-direction)")
    plt.plot(e_vals, Ft, label=r"$F_t$ (tangential, y-direction)")
    plt.xlabel("Hull offset e [m]")
    plt.ylabel("Force on hull [N]")
    plt.title("Wedge forces on hull vs offset (gap 0, laminar model)")
    plt.legend()
    plt.grid(True)

    # 2) Force magnitude vs offset
    plt.figure()
    plt.plot(e_vals, Fmag)
    plt.xlabel("Hull offset e [m]")
    plt.ylabel("Force magnitude |F| [N]")
    plt.title("Total wedge force magnitude on hull vs offset")
    plt.grid(True)

    # 3) Ratio |Fr| / Ft vs offset (to see how radial stiffens faster)
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

    plt.show()


if __name__ == "__main__":
    main()

