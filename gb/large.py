from math import pi

from gb.constants import Gval, atm, T_air, Rsp_air

from scipy.integrate import solve_ivp


def Pg(r, x, Rsp, T):
    """Definition of system described in post:
    https://gravitationalballoon.blogspot.com/2013/10/inclusion-of-air-pressure-effects-for.html
    P'(r) = - g(r) P(r) / (Rsp T)
    g'(r) = 4 G pi / (Rsp T) P(r) - 2 g(r) / r
    but written in somewhat generalized rk4 language, meaning x = [P(r), g(r)]
    """
    P_of_r = x[0]
    g_of_r = x[1]
    if g_of_r == 0.:
        g_over_r = 0.  # prevent division by zero errors, we know it is well behaved at center
    else:
        g_over_r = g_of_r / r
    return [
        -(g_of_r * P_of_r / (Rsp * T)),
        (4.0 * pi / (Rsp * T)) * Gval * P_of_r - 2 * g_over_r,
    ]


def F_air(r, x):
    """System defined for air specifically"""
    return Pg(r, x, Rsp_air, T_air)


def P_air(R, P0=atm):
    """Gives Pressure of air as a function of radius after solving system
    Uses standard gravity balloon notation that R denotes radius of central air sphere
    """
    sol = solve_ivp(F_air, [0., R], [P0, 0.])
    return sol.y[0][-1]
