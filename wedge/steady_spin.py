import numpy as np


def torque_coefficients(mu, length, radii, clearances):
    """
    Return the Couette torque coefficient for each gap:

        coeff_i = 2π μ L R_i^3 / c_i

    radii: array of shell inner radii, length = N_SHELLS
    clearances: array of gap widths, length = N_SHELLS - 1
    """
    radii = np.asarray(radii, dtype=float)
    clearances = np.asarray(clearances, dtype=float)
    if radii.size < 2 or clearances.size != radii.size - 1:
        raise ValueError("Expected radii length N and clearances length N-1.")
    if np.any(clearances <= 0.0):
        raise ValueError("All clearances must be positive.")
    r_inner = radii[:-1]
    return (2.0 * np.pi * mu * length * r_inner**3) / clearances


def steady_state_omegas(radii, clearances, mu, length, omega_inner, omega_outer,
                        tol=1e-12, max_iter=10000):
    """
    Solve for steady-state angular speeds such that the viscous torque transmitted
    through every gap is identical (torque equilibrium for intermediate shells).

    Uses a Gauss-Seidel relaxation on the balance:

        coeff_{i-1} (ω_{i-1} - ω_i) = coeff_i (ω_i - ω_{i+1})

    Returns: array of ω_i, length = len(radii).
    """
    radii = np.asarray(radii, dtype=float)
    clearances = np.asarray(clearances, dtype=float)
    n = radii.size
    if n < 2 or clearances.size != n - 1:
        raise ValueError("Expected radii length N and clearances length N-1.")

    coeffs = torque_coefficients(mu, length, radii, clearances)
    omegas = np.linspace(omega_inner, omega_outer, n)
    omegas[0] = omega_inner
    omegas[-1] = omega_outer

    for _ in range(max_iter):
        max_delta = 0.0
        for i in range(1, n - 1):
            coeff_in = coeffs[i - 1]
            coeff_out = coeffs[i]
            denom = coeff_in + coeff_out
            if denom == 0.0:
                continue
            new_val = (coeff_in * omegas[i - 1] + coeff_out * omegas[i + 1]) / denom
            delta = abs(new_val - omegas[i])
            max_delta = max(max_delta, delta)
            omegas[i] = new_val
        if max_delta < tol:
            break
    else:
        raise RuntimeError("steady_state_omegas did not converge.")

    return omegas


def torque_factor_from_offset(eccentricity, clearance):
    """
    Returns the multiplicative factor 1/sqrt(1 - eps^2) from lit/torque.md.
    """
    if clearance <= 0.0:
        raise ValueError("clearance must be positive")
    eps = float(eccentricity) / float(clearance)
    if eps >= 1.0:
        raise ValueError("Eccentricity exceeds clearance in torque computation.")
    if eps <= 0.0:
        return 1.0
    return 1.0 / np.sqrt(1.0 - eps**2)


def signed_torque_on_inner(omega_inner, omega_outer, coeff, eccentricity, clearance):
    """
    Torque exerted by the fluid on the inner shell (retarding if omega_inner > omega_outer).
    """
    factor = torque_factor_from_offset(eccentricity, clearance)
    delta = omega_inner - omega_outer
    # Positive delta => fluid drags inner shell backward => torque < 0
    return -coeff * delta * factor


if __name__ == "__main__":
    import sys

    # Ensure positional_250 reuses this module instance if it imports steady_spin.
    sys.modules.setdefault("steady_spin", sys.modules[__name__])

    from positional_250 import (
        R,
        C,
        MU,
        L,
        V_HULL,
        R_HULL,
    )

    omega_inner = V_HULL / R_HULL
    omega_outer = 0.0
    coeffs = torque_coefficients(MU, L, R, C)
    omegas = steady_state_omegas(R, C, MU, L, omega_inner, omega_outer)
    linear_speeds = omegas * R
    gap_torques = coeffs * (omegas[:-1] - omegas[1:])

    print("Steady-state shell speeds:")
    print(" idx |   radius [m] |    omega [rad/s] |   v [m/s]")
    for i, (radius, omega, speed) in enumerate(zip(R, omegas, linear_speeds)):
        print(f"{i:4d} | {radius:12.4f} | {omega:16.8f} | {speed:9.4f}")

    print("\nGap torques (should match):")
    for i, torque in enumerate(gap_torques):
        print(f"gap {i:02d}: {torque:.6e} N·m")
