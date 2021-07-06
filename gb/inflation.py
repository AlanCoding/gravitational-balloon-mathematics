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

    @staticmethod
    def t_P_small_large(P, rho=constants.rho):
        """Solves for t in terms of P
        P = G rho^2 pi (2/3) t^2 (3 R+t)/(R+t)
        for R << t (small),      and then R >> t, resolving to
        P = G rho^2 pi (2/3) t^2 and P = G rho^2 pi 2 t^2
        """
        core_term = LimitCases.t_P_core_term(P, rho)
        return (
            core_term / sqrt(2./3.),  # small
            core_term / sqrt(2),      # large
        )

    @staticmethod
    def t_RM_small_large(R, M, rho=constants.rho):
        """Solves for t in terms of R and M
        M = 4/3 pi ((R+t)^3 - R^3)
        for R << t (small),     and then R >> t (large)
        M = 4/3 pi t^3          M = 4/3 pi t R^2
        """
        core_term = M * 3. / (4. * pi)
        return (
            core_term**(1./3.),  # small
            core_term / (R**2 + 1),  # large
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

    # t_small, t_large = LimitCases.t_RM_small_large(R, M, rho=rho)
    R0 = (M * 3. / (4. * pi))**(1./3.)
    # P_small = P_Rt(R, t_small)
    # P_large = P_Rt(R, t_large)
    # guess_vector = (0.5 * (P_small + P_large), 0.5 * (t_small + t_large))
    guess_vector = (P_Rt(R, R0, rho=rho), R0)

    result = fsolve(residuals, guess_vector)
    return result


def P_RM(R, M, rho=constants.rho):
    return Pt_RM(R, M, rho)[0]
