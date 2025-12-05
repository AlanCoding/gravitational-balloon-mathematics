import numpy as np

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

# For simplicity: linearly staged shell speeds from V_HULL down to 0
# so each gap sees the same ΔU
shell_linear_speed = np.array([
    V_HULL * (1.0 - i / (N_SHELLS - 1)) for i in range(N_SHELLS)
], dtype=float)

# Relative speed in each gap (inner shell i vs outer shell i+1)
U_rel = np.abs(shell_linear_speed[:-1] - shell_linear_speed[1:])  # length 16
# With the linear profile above, all entries should be equal to V_HULL / (N_SHELLS-1)

# Clearances per gap (could be nonuniform later)
C = np.full(N_SHELLS - 1, GAP, dtype=float)


# ---------------------------
# Single-gap wedge force law
# ---------------------------

def gap_force_magnitudes(e, c, mu, u_rel, L):
    """
    Return (Fr, Ft) for a single short bearing gap,
    using the laminar wedge formulas in terms of the
    relative center offset e and clearance c.

    Fr: radial component (negative = inward reaction)
    Ft: tangential component (in direction of rotation / ΔU)
    """
    if e <= 0.0:
        return 0.0, 0.0

    eps = e / c
    if eps >= 1.0:
        raise ValueError(f"Offset e={e} exceeds or equals clearance c={c}")

    # Characteristic force scale:
    # F0 ~ mu * (ΔU) * L^3 / c^2   (generalized from mu*Ω*R*L^3/c^2 by ΩR -> ΔU)
    F0 = mu * u_rel * (L ** 3) / (c ** 2)

    denom_r = (1.0 - eps**2)**2
    denom_t = (1.0 - eps**2)**1.5

    Fr = -F0 * (eps**2) / denom_r
    Ft = +F0 * (np.pi * eps / 4.0) / denom_t

    return Fr, Ft


def gap_force_vector(r_inner, r_outer, c, mu, u_rel, L):
    """
    Compute the 2D force vector on the INNER shell due to the fluid
    in the gap between (inner, outer) shells.

    r_inner, r_outer: np.array([x,y]) center coordinates of the shells.
    c: clearance for this gap
    mu: viscosity
    u_rel: relative linear speed across the gap
    L: axial length
    """
    d = r_inner - r_outer
    e = np.linalg.norm(d)

    if e == 0.0:
        # Perfectly concentric -> no net wedge force at this level
        return np.zeros(2)

    er = d / e                          # radial unit (inner->outer)
    et = np.array([-er[1], er[0]])      # tangential unit (+90° rotation)

    Fr, Ft = gap_force_magnitudes(e, c, mu, u_rel, L)

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

        F_inner = gap_force_vector(
            r_inner=r_inner,
            r_outer=r_outer,
            c=C[i],
            mu=MU,
            u_rel=U_rel[i],
            L=L,
        )

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
