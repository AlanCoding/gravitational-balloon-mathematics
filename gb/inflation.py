from . import constants

from scipy.optimize import fsolve

from math import sqrt, pi


def M_Rt(R, t):
    return constants.rho * (4./3.) * pi * ((R + t)**3 - R**3)


def P_Rt(R, t):
    scale_term = constants.Gval * constants.rho**2 * pi
    return scale_term * (2./3.) * t**2 * (3 * R + t) / (R + t)


def t_RP(R, P):
    def residual_t(t):
        return (P - P_Rt(R, t))

    t_guess = 1.366 * sqrt(P / (2 * constants.Gval * pi)) / constants.rho

    result = fsolve(residual_t, t_guess)
    return result[0]
