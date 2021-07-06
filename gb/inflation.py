from . import constants

from scipy.optimize import fsolve

from math import sqrt, pi


# For derivations see post:
# https://gravitationalballoon.blogspot.com/2021/07/a-more-detailed-run-through-of-pressure.html


def M_Rt(R, t, rho=constants.rho):
    """Authoritative encoding of the mass equation: M = 4/3 pi rho ((R+t)^3 - R^3)"""
    return rho * (4./3.) * pi * ((R + t)**3 - R**3)


def P_Rt(R, t, rho=constants.rho):
    """Authoritative encoding of the pressure equation: P = 2/3 G rho^2 pi t^2 (3 R+t)/(R+t)"""
    scale_term = constants.Gval * rho**2 * pi
    return scale_term * (2./3.) * t**2 * (3 * R + t) / (R + t)


class LimitCases:
    @staticmethod
    def t_P_small_large(P, rho=constants.rho):
        """Gives approximations for t in terms of P
        Solves for t in terms of P
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
        for R << t (small),      and then R >> t, resolving to
        P = G rho^2 pi (2/3) t^2 and P = G rho^2 pi 2 t^2
        """
        core_term = sqrt(P / (2 * constants.Gval * pi)) / rho
        return (
            core_term / sqrt(2./3.),  # small
            core_term / sqrt(2),      # large
        )


def t_RP(R, P, rho=constants.rho):
    def residual_t(t):
        return (P - P_Rt(R, t, rho=rho))

    t_small, t_large = LimitCases.t_P_small_large(P, rho=rho)
    t_guess = 0.5 * (t_small + t_large)

    result = fsolve(residual_t, t_guess)
    return result[0]


def Pt_RM(R, M, rho=constants.rho):
    def residuals(state):
        P, t = state
        return (
            M - M_Rt(R, t, rho=rho),
            P - P_Rt(R, t, rho=rho)
        )

    # guess made using numbers from uninflated case: M = 4/3 pi rho t^3
    R0 = (M * 3. / (4. * pi))**(1./3.)
    guess_vector = (P_Rt(R, R0, rho=rho), R0)

    result = fsolve(residuals, guess_vector)
    return result


def P_RM(R, M, rho=constants.rho):
    return Pt_RM(R, M, rho)[0]
