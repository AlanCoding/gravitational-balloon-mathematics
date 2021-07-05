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
    def t_P_limit(P, alpha, rho=constants.rho):
        """Solves P = G rho^2 pi alpha t^2 for t, where alpha is for scenario"""
        return sqrt(P / (2 * constants.Gval * pi)) / rho

    def t_P_small(P, rho=constants.rho):
        """solves
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
        where R << t, resolving to
        P = G rho^2 pi (2/3) t^2
        """
        return LimitCases.t_P_limit(P, 2./3., rho)

    def t_P_large(P, rho=constants.rho):
        """solves
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t), where R >> t, resolving to
        P = G rho^2 pi 2 t^2
        """
        return LimitCases.t_P_limit(P, 2., rho)


def t_RP(R, P, rho=constants.rho):
    def residual_t(t):
        return (P - P_Rt(R, t, rho=rho))

    t_min = LimitCases.t_P_small(P, rho=rho)
    t_max = LimitCases.t_P_large(P, rho=rho)

    t_guess = 0.5 * (t_min + t_max)

    result = fsolve(residual_t, t_guess)
    return result[0]
