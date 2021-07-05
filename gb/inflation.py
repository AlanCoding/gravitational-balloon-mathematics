from . import constants

from scipy.optimize import fsolve

from math import sqrt, pi


def M_Rt(R, t, rho=constants.rho):
    return rho * (4./3.) * pi * ((R + t)**3 - R**3)


def P_Rt(R, t, rho=constants.rho):
    scale_term = constants.Gval * rho**2 * pi
    return scale_term * (2./3.) * t**2 * (3 * R + t) / (R + t)


class LimitCases:
    @staticmethod
    def t_P_core_term(P, rho=constants.rho):
        """Solves P = G rho^2 pi t^2 for t"""
        return sqrt(P / (2 * constants.Gval * pi)) / rho

    def t_P_small_large(P, rho=constants.rho):
        """solves
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
        for R << t (small),      and then R >> t, resolving to
        P = G rho^2 pi (2/3) t^2 and P = G rho^2 pi 2 t^2
        """
        core_term = LimitCases.t_P_core_term(P, rho)
        return (core_term / sqrt(2./3.), core_term / sqrt(2))


def t_RP(R, P, rho=constants.rho):
    def residual_t(t):
        return (P - P_Rt(R, t, rho=rho))

    t_small, t_large = LimitCases.t_P_small_large(P, rho=rho)
    t_guess = 0.5 * (t_small + t_large)

    result = fsolve(residual_t, t_guess)
    return result[0]
