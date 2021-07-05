from . import constants

from scipy.optimize import fsolve

from math import sqrt, pi


def M_Rt(R, t):
    return constants.rho * (4./3.) * pi * ((R + t)**3 - R**3)


def P_Rt(R, t):
    scale_term = constants.Gval * constants.rho**2 * pi
    return scale_term * (2./3.) * t**2 * (3 * R + t) / (R + t)


class LimitCases:
    @staticmethod
    def t_P_limit(P, alpha):
        """Solves P = G rho^2 pi alpha t^2 for t, where alpha is for scenario"""
        return sqrt(P / (2 * constants.Gval * pi)) / constants.rho

    def t_P_small(P):
        """solves
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
        where R << t, resolving to
        P = G rho^2 pi (2/3) t^2
        """
        return LimitCases.t_P_limit(P, 2./3.)

    def t_P_large(P):
        """solves
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t), where R >> t, resolving to
        P = G rho^2 pi 2 t^2
        """
        return LimitCases.t_P_limit(P, 2.)


def t_RP(R, P):
    def residual_t(t):
        return (P - P_Rt(R, t))

    t_min = LimitCases.t_P_small(P)
    t_max = LimitCases.t_P_large(P)

    t_guess = 0.5 * (t_min + t_max)

    result = fsolve(residual_t, t_guess)
    return result[0]
