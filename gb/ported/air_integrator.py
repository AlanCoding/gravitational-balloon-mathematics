# "Gas Giant" planetary physics analysis code
#   Start with some central pressure, then this code integrates
#  the system of differential equations to predict the gas pressure
#  and gravitational field throughout the interior of that planet.
#
#   Intended to produce numbers for the fictional world Virga, with
#  two example cases where the central pressure is 1 atmosphere and
#  then 3 atmospheres. Spatial data is outputed to files.
#   Parameters are also put in place for Jupiter and the sun, but these
#  cases have a problem with spatial resolution near the center.
#  With 10000 spatial points, Jupiter can be resolved to some extent but
#  not the sun.
from math import pi

from gb.constants import Gval, kB, amu, T_air, FM_air, Rsp_air


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


def main():
    summary = {}

    r_max = 1.0e8
    r_step = r_max / 10000

    print(" R specific for air ")
    print(" using: " + str(Rsp_air))
    print(" calc: " + str(kB / (FM_air * amu)))

    # normal case
    x = [1.0e5, 0.0]
    r = 100.0
    data = []
    while True:
        data.append([r] + x)
        xold = x
        x = rk4(F_air, xold, r, r_step)
        r = r + r_step
        if r > r_max:
            break
    summary["1atm"] = data

    # high pressure case
    x = [3.0e5, 0.0]
    r = 100.0
    data = []
    while True:
        data.append([r] + x)
        xold = x
        x = rk4(F_air, xold, r, r_step)
        r = r + r_step
        if r > r_max:
            break
    summary["3atm"] = data

    # Jupiter case
    Rsp = kB / ((1.0 * 0.898 + 4.0 * 0.102 + 16.04 * 0.003) * amu)
    T = 293.0  # Kelvin
    print(" jupiter Rsp " + str(Rsp))

    def F_jupiter(r, x):
        return Pg(r, x, Rsp, T)

    x = [1.0e5 * 100.0e6, 0.0]  # 6 million atmospheres at center
    r = 100.0
    data = []
    while True:
        data.append([r] + x)
        xold = x
        x = rk4(F_jupiter, xold, r, r_step)
        r = r + r_step
        if r > r_max:
            break
    summary["jupiter"] = data

    # Sun case
    Rsp = kB / ((1.0 * 0.912 + 4.0 * 0.087 + 16.0 * 0.0097) * amu)
    print(f"  sun Rsp {Rsp}")
    T = 5500.0

    def F_sun(r, x):
        return Pg(r, x, Rsp, T)

    x = [1.0e5 * 2.5e11, 0.0]
    r = 100.0
    data = []
    while True:
        data.append([r] + x)
        xold = x
        x = rk4(F_sun, xold, r, r_step)
        r = r + r_step
        if r > r_max:
            break
    summary["sun"] = data

    for scenario, data in summary.items():
        print("")
        fname = f'{scenario}.txt'
        print(f"Writing data for {scenario} scenario to {fname} file")
        with open(fname, 'w') as f:
            f.write("radius    pressure    field\n")
            for line in data:
                f.write('  '.join([str(val) for val in line]) + '\n')


def rk4(F, x0, t0, delt):
    """Just another implementation of rk4"""
    k1 = F(t0,              x0)
    k2 = F(t0 + 0.5 * delt, [x0[i] + k1[i] * delt / 2.0 for i in range(2)])
    k3 = F(t0 + 0.5 * delt, [x0[i] + k2[i] * delt / 2.0 for i in range(2)])
    k4 = F(t0 + delt,       [x0[i] + k3[i] * delt for i in range(2)])
    #   write(*,*) ' k ',k1,k2,k3,k4
    return [x0[i] + (k1[i] + 2 * k2[i] + 2 * k3[i] + k4[i]) * delt / (6.0) for i in range(2)]


if __name__ == '__main__':
    main()
