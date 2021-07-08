# Thermal hydraulic functions
def c_f(Re):
    b = -0.05
    kappa = 0.41
    f_min = Exp(-2 * b * kappa - Log(Re ^ 2 / 2))
    f_max = ((Log(10) + 1) / (2 * Log(Re / 2.51))) ^ 2
    n = 0

    while True:
        n = n + 1
        f = (f_min + f_max) / 2
        g_middle = 1 / kappa * Log(Re * (f / 2) ^ (1 / 2)) + b - (2 / f) ^ (1 / 2)
        g_lower = 1 / kappa * Log(Re * (f_min / 2) ^ (1 / 2)) + b - (2 / f_min) ^ (
            1 / 2
        )
        if g_middle == 0 or (f_max - f_min) / 2 < 1e-06:
            break
        else:
            if g_middle * g_lower > 0:
                f_min = f
            else:
                f_max = f

        c_f = f
        if n > 100:
            c_f = CVErr(xlErrNA)
            break
    return c_f


# Useful implementation of Colebrook-White equation solver
def Colebrook2(Rr, Re):
    f_min = (2.51 / Re) ^ 2 * (1 - Rr / 3.7) ^ (-2)
    f_max = ((2.51 / Re + Log(10) / 2) / (1 - Rr / 3.7)) ^ 2
    n = 0

    while True:
        n = n + 1
        f = (f_min + f_max) / 2
        g_middle = -2 / Log(10) * Log(Rr / 3.7 + 2.51 / Re * f ^ (-1 / 2)) - f ^ (
            -1 / 2
        )
        g_lower = -2 / Log(10) * Log(
            Rr / 3.7 + 2.51 / Re * f_min ^ (-1 / 2)
        ) - f_min ^ (-1 / 2)
        if g_middle == 0 or (f_max - f_min) / 2 < 1e-06:
            break
        else:
            if g_middle * g_lower > 0:
                f_min = f
            else:
                f_max = f

        Colebrook2 = f
        if n > 100:
            Colebrook2 = CVErr(xlErrNA)
            break
    return Colebrook2


def Colebrook(Re, a, b):
    aa = 1 / (Re ^ 2 * Exp(2 * b / a))
    bb = (a + Re) ^ 2 / (Re ^ 2 * (a + b) ^ 2)
    n = 0
    while True:
        n = n + 1
        c = (aa + bb) / 2
        Fc = g_Colebrook(c, Re, a, b)
        Fa = g_Colebrook(aa, Re, a, b)
        if Fc == 0 or (bb - aa) / 2 < 1e-06:
            break
        else:
            if Fc * Fa > 0:
                aa = c
            else:
                bb = c

        Colebrook = c
        if n > 100:
            Colebrook = -2
            break


def g_Colebrook(f, Re, a, b):
    return a * Log(Re * (f) ^ (1 / 2)) + b - (f) ^ (-1 / 2)


# Supporting function used for layered rotating cylinders
def GeometricSeries(x, i):
    GeometricSeries = 0
    for ii in range(i + 1):
        GeometricSeries = GeometricSeries + x ^ ii
    return GeometricSeries
