from . import constants

from scipy.optimize import fsolve

from math import sqrt, pi


# For derivations see post:
# https://gravitationalballoon.blogspot.com/2021/07/a-more-detailed-run-through-of-pressure.html


# --- System definition methods ---
def M_Rt(R, t, rho=constants.rho):
    """Authoritative encoding of the mass equation: M = 4/3 pi rho ((R+t)^3 - R^3)"""
    return rho * (4./3.) * pi * ((R + t)**3 - R**3)


def P_Rt(R, t, rho=constants.rho):
    """Authoritative encoding of the pressure equation: P = 2/3 G rho^2 pi t^2 (3 R+t)/(R+t)"""
    scale_term = constants.Gval * rho**2 * pi
    return scale_term * (2./3.) * t**2 * (3 * R + t) / (R + t)


# --- System solution methods ---
def t_P_large(P, rho=constants.rho):
    """Make educated guess of thickness from pressure"""
    return sqrt(P / (2 * constants.Gval * pi)) / rho


def t_P_small(P, rho=constants.rho):
    return t_P_large(P, rho=rho) / sqrt(3.)


def t_RP(R, P, rho=constants.rho):  # tested
    def residual_t(t):
        return (P - P_Rt(R, t, rho=rho))

    # limit cases of: P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
    # (3 R+t)/(R+t) = 3     for R >> t     --> P = G (t rho)^2 pi 2         large
    # (3 R+t)/(R+t) = 1     for R << t     --> P = G (t rho)^2 pi (2/3)     small
    # t_guess = 0.5 * (1./sqrt(2.) + 1./sqrt(2./3.)) * sqrt(P / (constants.Gval * pi)) / rho
    t_guess = t_P_large(P, rho=rho)

    result = fsolve(residual_t, t_guess)
    return result[0]


def R_Mt(M, t, rho=constants.rho):
    def residual_R(R):
        return (M - M_Rt(R, t, rho=rho))

    R_guess = 0.5 * t

    result = fsolve(residual_R, R_guess)
    return result[0]


def R_Pt(P, t, rho=constants.rho):
    def residual_R(R):
        return (P - P_Rt(R, t, rho=rho))

    result = fsolve(residual_R, 0.)
    return result[0]


def R0_M(M, rho=constants.rho):
    """Small central volume (uninflated), simple geometric case of sphere: M = 4/3 pi rho t^3"""
    return (M * 3. / (4. * pi * rho))**(1./3.)


def Pt_RM(R, M, rho=constants.rho):  # tested
    def residuals(state):
        P, t = state
        return (
            M - M_Rt(R, t, rho=rho),
            P - P_Rt(R, t, rho=rho)
        )

    R0 = R0_M(M, rho=rho)  # wall thickness set to uninflated radius, small limit
    guess_vector = (P_Rt(R, R0, rho=rho), R0)

    result = fsolve(residuals, guess_vector)
    return result


def Rt_MP(M, P, rho=constants.rho):
    def residuals(state):
        R, t = state
        return (
            M - M_Rt(R, t, rho=rho),
            P - P_Rt(R, t, rho=rho)
        )

    # alpha - a metric of how inflated it is
    # lower value indicates more inflated
    R0 = R0_M(M, rho=rho)
    P0 = P_Rt(0., R0, rho=rho)
    alpha = P / P0

    t_large = t_P_large(P, rho=rho)
    t_small = t_P_small(P, rho=rho)
    R_large = R_Mt(M, t_large, rho=rho)

    guess_vector = (
        (1. - alpha) * R_large,  # R_small would be 0
        alpha * t_small + (1. - alpha) * t_large
    )

    result = fsolve(residuals, guess_vector)
    return result


# --- Trivial conversions for completeness ---
def P_RM(*args, **kwargs):  # tested
    return Pt_RM(*args, **kwargs)[0]


def t_RM(*args, **kwargs):
    return Pt_RM(*args, **kwargs)[1]


def R_MP(*args, **kwargs):
    return Rt_MP(*args, **kwargs)[0]


def t_MP(*args, **kwargs):
    return Rt_MP(*args, **kwargs)[1]


def M_RP(R, P, *args, **kwargs):
    t = t_RP(R, P, *args, **kwargs)
    return M_Rt(R, t, *args, **kwargs)


def P_VM(V, M, *args, **kwargs):
    R = (V * 3. / (4. * pi))**(1./3.)
    return Pt_RM(R, M, *args, **kwargs)[0]
