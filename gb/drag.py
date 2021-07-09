from math import sqrt, log
from functools import partial

from scipy.optimize import bisect


def colebrook_residual(Rr, Re, f):
    # Colebrook-White equation
    # https://gravitationalballoon.blogspot.com/2013/03/a-robust-method-for-numerical-solution.html
    # https://en.wikipedia.org/wiki/Darcy_friction_factor_formulae#Colebrook%E2%80%93White_equation
    return -2 / log(10.) * log(Rr / 3.7 + 2.51 / (Re * sqrt(f))) - 1. / sqrt(f)


def f_colebrook(Rr, Re):
    # bounds from:
    # https://gravitationalballoon.blogspot.com/2013/03/good-set-of-bounds-for-colebrook-white.html
    f_min = (2.51 / Re)**2 * (1 - Rr / 3.7)**(-2)
    f_max = ((2.51 / Re + log(10) / 2) / (1 - Rr / 3.7))**2

    f_residual = partial(colebrook_residual, Rr, Re)

    return bisect(f_residual, f_min, f_max)
