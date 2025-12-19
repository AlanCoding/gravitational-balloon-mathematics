import numpy as np

try:
    from scipy.integrate import cumulative_trapezoid, simpson
except ImportError:
    def cumulative_trapezoid(y, x, initial=0.0):
        y = np.asarray(y)
        x = np.asarray(x)
        if y.size != x.size:
            raise ValueError("y and x must have the same length")
        if y.size < 2:
            return np.zeros_like(y)

        trap = 0.5 * (y[1:] + y[:-1]) * np.diff(x)
        cumsum = np.cumsum(trap)
        if initial is None:
            return cumsum
        return np.concatenate(([initial], initial + cumsum))

    def simpson(y, x):
        y = np.asarray(y)
        x = np.asarray(x)
        n = y.size
        if n < 2:
            return 0.0
        if n % 2 == 0:
            raise ValueError("Simpson integration requires an odd number of samples.")
        h = (x[-1] - x[0]) / (n - 1)
        return (h / 3.0) * (
            y[0] + y[-1]
            + 4.0 * np.sum(y[1:-1:2])
            + 2.0 * np.sum(y[2:-2:2])
        )

# ---------------------------
# Physical / geometric params
# ---------------------------

N_SHELLS = 17        # shells 0..16 -> 16 gaps
N_DOFS   = 2 * N_SHELLS  # x,y for each shell

# Geometry: hull and friction buffers
R_HULL = 250.0       # m, inner habitat radius
GAP    = 6.0         # m, nominal radial clearance between shells
L      = 1000.0      # m, axial length of the cylinders (tweakable)

# Radii of each shell (inner surface of each shell)
R = np.array([R_HULL + i * GAP for i in range(N_SHELLS)], dtype=float)

# Fluid properties (air-ish)
MU = 1.8e-5          # Pa*s

# Rim speed of hull (at R_HULL)
V_HULL = 50.0        # m/s

from steady_spin import steady_state_omegas, torque_coefficients

# Clearances per gap (could be nonuniform later)
C = np.full(N_SHELLS - 1, GAP, dtype=float)

# Steady-state angular speeds derived from torque balance
OMEGA_INNER = V_HULL / R_HULL
OMEGA_OUTER = 0.0
TORQUE_COEFFS = torque_coefficients(MU, L, R, C)
SHELL_OMEGA_STEADY = steady_state_omegas(
    R,
    C,
    MU,
    L,
    OMEGA_INNER,
    OMEGA_OUTER,
)

# Corresponding tangential surface speeds
shell_linear_speed = SHELL_OMEGA_STEADY * R

# Relative baseline slip per gap (inner shell i vs outer shell i+1)
U_rel = np.abs(shell_linear_speed[:-1] - shell_linear_speed[1:])

FR_FUDGE = 1.0  # multiplier on radial force component


# Pre-compute a θ-grid for the long-bearing integrals
N_THETA = 2049  # odd number so Simpson's rule applies cleanly
THETA_GRID = np.linspace(0.0, 2.0 * np.pi, N_THETA, endpoint=True)
COS_THETA = np.cos(THETA_GRID)
SIN_THETA = np.sin(THETA_GRID)
TWO_PI = 2.0 * np.pi


def set_radial_fudge_factor(value: float) -> None:
    """
    Set a global multiplier for the radial force component.
    """
    global FR_FUDGE
    FR_FUDGE = float(value)


# ---------------------------
# Single-gap wedge force law
# ---------------------------

def _long_bearing_pressure_components(e, c, mu, u_rel, L, r_inner):
    """
    Compute the pressure-induced force components for a single gap using
    the long-bearing Reynolds solution described in lit/radial.md.

    Returns (Fr, Ft) expressed in the local (er, et) basis, where er is
    along the line of centers (inner → outer) and et is rotated +90°.
    Negative pressures (tension) are clipped to zero via a Reynolds boundary.
    """
    eps = e / c
    h = c * (1.0 + eps * COS_THETA)

    inv_h2 = 1.0 / (h * h)
    inv_h3 = inv_h2 / h

    # 6 * μ * ω * R^2 with ω replaced by U_rel / R
    load_scale = 6.0 * mu * u_rel * r_inner

    integral_inv_h2 = simpson(inv_h2, THETA_GRID)
    integral_inv_h3 = simpson(inv_h3, THETA_GRID)

    if not np.isfinite(integral_inv_h3) or np.isclose(integral_inv_h3, 0.0):
        raise ValueError("Degenerate integral encountered in radial force computation.")

    integration_constant = -load_scale * (integral_inv_h2 / integral_inv_h3)

    dp_dtheta = (load_scale * h + integration_constant) * inv_h3

    # Integrate once more for pressure; remove mean to avoid accumulating drift.
    p_theta = cumulative_trapezoid(dp_dtheta, THETA_GRID, initial=0.0)
    avg_pressure = simpson(p_theta, THETA_GRID) / TWO_PI
    p_theta -= avg_pressure
    # Enforce Reynolds boundary (no tensile stress) by ignoring the
    # portion of the film that would be in tension.
    p_positive = np.clip(p_theta, 0.0, None)
    if np.all(p_positive == 0.0):
        return 0.0, 0.0

    scale = r_inner * L
    Fr = scale * simpson(p_positive * COS_THETA, THETA_GRID)
    Ft = scale * simpson(p_positive * SIN_THETA, THETA_GRID)
    return Fr, Ft


def gap_force_magnitudes(e, c, mu, u_rel, L, r_inner):
    """
    Return (Fr, Ft) for a single gap using the long-bearing
    Reynolds solution for the radial component and the shear-based
    tangential load from lit/tangental.md.

    Fr: radial component (negative = inward reaction)
    Ft: tangential component (in direction of rotation / ΔU)
    """
    if e <= 0.0:
        return 0.0, 0.0

    eps = e / c
    if eps >= 1.0:
        raise ValueError(f"Offset e={e} exceeds or equals clearance c={c}")

    Fr, Ft = _long_bearing_pressure_components(e, c, mu, u_rel, L, r_inner)
    Fr *= FR_FUDGE

    return Fr, Ft


def gap_force_vector(r_inner_center, r_outer_center, c, mu, u_rel, L, r_inner_radius):
    """
    Compute the 2D force vector on the INNER shell due to the fluid
    in the gap between (inner, outer) shells.

    r_inner_center, r_outer_center: np.array([x,y]) center coordinates of the shells.
    c: clearance for this gap
    mu: viscosity
    u_rel: relative linear speed across the gap
    L: axial length
    """
    d = r_inner_center - r_outer_center
    e = np.linalg.norm(d)

    if e == 0.0:
        # Perfectly concentric -> no net wedge force at this level
        return np.zeros(2)

    er = d / e                          # radial unit (inner->outer)
    et = np.array([-er[1], er[0]])      # tangential unit (+90° rotation)

    Fr, Ft = gap_force_magnitudes(e, c, mu, u_rel, L, r_inner_radius)

    F_vec = Fr * er + Ft * et
    return F_vec


# ---------------------------
# Multi-shell total fluid forces
# ---------------------------

def total_fluid_forces(q, C, MU, U_rel, L):
    """
    Compute fluid wedge forces on all shells for a given configuration q.

    q: shape (2*N_SHELLS,), [x0,y0,x1,y1,...,x16,y16]
    C: array of clearances for each gap, length = N_SHELLS - 1
    U_rel: array of relative speeds per gap, length = N_SHELLS - 1
    MU: viscosity
    L: axial length

    Returns: F, same shape as q, fluid force on each shell (inner + outer contributions).
    """
    F = np.zeros_like(q)

    for i in range(N_SHELLS - 1):
        # Inner & outer shell center positions
        r_inner = q[2*i:2*i+2]
        r_outer = q[2*(i+1):2*(i+1)+2]

        try:
            F_inner = gap_force_vector(
                r_inner_center=r_inner,
                r_outer_center=r_outer,
                c=C[i],
                mu=MU,
                u_rel=U_rel[i],
                L=L,
                r_inner_radius=R[i],
            )
        except ValueError as exc:
            raise ValueError(
                f"gap {i} between shells {i} and {i+1}: {exc}"
            ) from exc

        # Add to inner, subtract from outer (action-reaction)
        F[2*i:2*i+2]      += F_inner
        F[2*(i+1):2*(i+1)+2] -= F_inner

    return F


# ---------------------------
# Numerical stiffness (Jacobian) builder
# ---------------------------

def build_stiffness_matrix(q0, C, MU, U_rel, L, h=1e-4):
    """
    Numerically build the stiffness matrix K at configuration q0,
    using central differences:

        F_fluid(q) = total_fluid_forces(...)
        K_{mn} = - dF_m / dq_n

    q0: base configuration, shape (2*N_SHELLS,)
    h: finite-difference step (meters)

    Returns: K, shape (2*N_SHELLS, 2*N_SHELLS)
    """
    n = q0.size
    K = np.zeros((n, n))

    F0 = total_fluid_forces(q0, C, MU, U_rel, L)

    for j in range(n):
        dq = np.zeros_like(q0)
        dq[j] = h

        F_plus  = total_fluid_forces(q0 + dq, C, MU, U_rel, L)
        F_minus = total_fluid_forces(q0 - dq, C, MU, U_rel, L)

        dF_dqj = (F_plus - F_minus) / (2.0 * h)

        # Stiffness convention: F ≈ F0 - K (q - q0)
        K[:, j] = -dF_dqj

    return K


# ---------------------------
# Example usage / test
# ---------------------------

if __name__ == "__main__":
    # Base configuration: all shells concentric at origin (no wedge force)
    q0 = np.zeros(N_DOFS)

    # Introduce a small offset of the innermost hull in +x (e.g. 0.1 m)
    q0[0] = 0.1  # shell 0, x-component

    F = total_fluid_forces(q0, C, MU, U_rel, L)
    print("Fluid forces on each shell (Fx,Fy):")
    for i in range(N_SHELLS):
        Fx, Fy = F[2*i:2*i+2]
        print(f"Shell {i:2d}: Fx = {Fx: .3e} N, Fy = {Fy: .3e} N")

    # Build stiffness matrix around this configuration
    K = build_stiffness_matrix(q0, C, MU, U_rel, L, h=1e-3)
    print("\nStiffness matrix K shape:", K.shape)
    # You can inspect eigenvalues, blocks, etc. as needed.
