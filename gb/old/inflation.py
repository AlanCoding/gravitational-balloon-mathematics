# manual rewrite, abandoned
# def P_Rt(R, t, rho):
#     return (2./3.) * constants.pi * constants.Gval * ((t * rho)**2) * (3 * R + t) / (R + t)
# def t_RP(R, P, rho):
#     val = 1.366 * sqrt( P / (2 * constants.Gval * constants.pi)) / rho
#     for i in range(20):
#         delta = -1.0 * (P_Rt(R, val, rho) - P) / dPdt_Rt(R, val, rho)
#         val = val + delta
#         if abs(delta / val) < 1.0e-6:
#             break
#     else:
#         raise RuntimeError(f'Surpassed iteration limit of t_RP, val: {val}')
#     return val

# ' Functions of constants
def Gval():
    return 6.67384e-11


def Pi():
    return 3.14159265358979


def AU():
    return 149597871000


def Skylab():
    return 34400


def atm():
    return 101325


def sun_mass():
    return 1.989e30


def Stefan_const():
    return 5.6704e-08


# ' Density approximation function
def density_type3(T1, T2):
    density_type3 = density_kra(T1)
    if density_type3 == 1300:
        density_type3 = density_kra(T2)
    return density_type3


def density_type2(T1, T2):
    density_type2 = density_type(T1)
    if density_type2 == 1300:
        density_type2 = density_type(T2)
    return density_type2


def density_kra(Tp):
    T = Tp[0].lower()
    c_array = Array("C", "D", "P", "T", "B", "G", "F")
    s_array = Array("S", "K", "Q", "V", "R", "A", "E")
    density_kra = 1300
    m_array = "M"
    for n in range(7):
        if T == c_array[n].lower():
            density_kra = 1380

        if T == s_array[n].lower():
            density_kra = 2710

    if T == LCase(m_array):
        density_kra = 5320
    return density_kra


def density_type(Tp):
    T_first = Tp[0].lower()
    density_type = -2
    if T_first == "c":
        density_type = 1166.76
    elif T_first == "s":
        density_type = 1985.445
    elif T_first == "m":
        density_type = 2766.776
    elif T_first == "v":
        density_type = 1456.6
    else:
        density_type = 1300
    return density_type


# ' function to find the radius of maximum N2 mass
def R_N2max(M, rho):
    n = 1
    if P_RM(0, M, rho) < 0.21 * atm():
        R_N2max = -3
    else:
        # '    R_N2max = R_MP(M, 0.21 * atm(), rho) ' first attempt
        dPdRp = dPdR_RM(0, M, rho)
        dPdR2 = (dPdR_RM(0.01, M, rho) - dPdRp) / 0.01
        R_N2max = Math.Sqr((0.21 * atm() - P_RM(0, M, rho)) * 3 / dPdR2)
        while True:
            dPdRp = dPdR_RM(R_N2max, M, rho)
            dPdR2 = (dPdR_RM(R_N2max + 0.01, M, rho) - dPdRp) / 0.01
            delta = -(P_RM(R_N2max, M, rho) - 0.21 * atm() + R_N2max * dPdRp / 3) / (
                4 * dPdRp / 3 + R_N2max * dPdR2 / 3
            )
            R_N2max = R_N2max + delta
            n = n + 1
            if abs(delta / R_N2max) < 1e-07:
                break
            elif n > 20:
                R_N2max = -2
                break

    return R_N2max


# ' Functions for solar system transfer orbits
def inclined_hoh_avg(a, i):
    inclined_hoh_avg = 0.5 * (inclined_hoh(a, i) + inclined_hoh_min(a, i))
    return inclined_hoh_avg


def inclined_hoh(a, i):
    v1 = hohmann1_mrr(sun_mass(), AU(), a * AU())
    ve = Math.Sqr(Gval() * sun_mass() / AU())
    gv = ve + v1
    v1p = Math.Sqr(ve ** 2 + gv ** 2 - 2 * gv * ve * Math.Cos(i * Pi() / 180.0))
    v2 = hohmann2_mrr(sun_mass(), AU(), a * AU())
    inclined_hoh = v1p + v2
    return inclined_hoh


def inclined_hoh_min(a, i):
    v1 = hohmann1_mrr(sun_mass(), AU(), a * AU())
    v2 = hohmann2_mrr(sun_mass(), AU(), a * AU())
    ve = Math.Sqr(Gval() * sun_mass() / (a * AU()))
    gv = ve - v2
    v2p = Math.Sqr(ve ** 2 + gv ** 2 - 2 * gv * ve * Math.Cos(i * Pi() / 180.0))
    inclined_hoh_min = v1 + v2p
    return inclined_hoh_min


def hohmann1_mrr(M, r1, r2):
    if r2 > r1:
        hohmann1_mrr = (Gval() * M / r1) ** (1 / 2) * (
            (2 * r2 / (r1 + r2)) ** (1 / 2) - 1
        )
    else:
        hohmann1_mrr = (Gval() * M / r1) ** (1 / 2) * (
            1 - (2 * r2 / (r2 + r1)) ** (1 / 2)
        )
    return hohmann1_mrr


def hohmann2_mrr(M, r1, r2):
    if r2 > r1:
        hohmann2_mrr = (Gval() * M / r2) ** (1 / 2) * (
            1 - (2 * r1 / (r1 + r2)) ** (1 / 2)
        )
    else:
        hohmann2_mrr = (Gval() * M / r2) ** (1 / 2) * (
            (2 * r1 / (r2 + r1)) ** (1 / 2) - 1
        )
    return hohmann2_mrr


# ' def returns the tether mass to payload mass ratio for rotating tether in space
def tether_rot(v, ss):
    tether_rot = 2  #
    alpha = v / Math.Sqr(2 * ss)
    tether_rot = (
        Pi() * alpha * Application.WorksheetFunction.Erf(alpha) * Math.Exp(alpha ** 2)
    )
    return tether_rot


# ' --- functions related to asteroid abundance ----
def dNdD_wiki(D):
    dNdD_wiki = 3762457.114 * D ** (
        -3.12063
    )  # ' asteroid size distribution from Wikipedia interpolation
    return dNdD_wiki


def dNdD_JPL(D):
    # ' asteroid size distribution using JPL search limited to certain range: about 131 km to 200
    dNdD_JPL = 762000000.0 * D ** (-3.6)
    return dNdD_JPL


def dNdD_MB(D):
    # ' asteroid size distribution using fitted def to main belt
    # ' distribution published in literature
    dNdD_MB = 6154110.296 * D ** (-3.183317186)
    return dNdD_MB


# ' Functions related to the absolute magnitude
def dia_p(H, P):
    dia_p = 1329.0 * 10 ** (-0.2 * H) / (P) ** (0.5)
    return dia_p


def dia(H):
    dia = 1329 * 10 ** (-0.2 * H) / (0.2) ** (0.5)
    return dia


def H_dia(dia):
    H_dia = -Log(dia * Math.Sqr(0.2) / 1329) / (0.2 * Log(10.0))
    return H_dia


def mass(H):
    mass = 1329.0 * 10 ** (-0.2 * H) / (0.2) ** (0.5)
    return mass


# ' Gravity balloon functions
def P_M(M, rho):
    return P_RM(0.0, M, rho)


def M_P_small(P, rho):
    return (
        P * (rho * 4 / 3 * Pi()) ** (2 / 3) / (2 / 3 * Gval() * rho ** 2 * Pi())
    ) ** (3 / 2)


# '----based on second revision of mathematics ---
# ' Functions based on (M,R,t) tripple
def M_Rt(R, T, rho):
    return (4.0 / 3.0) * Pi() * rho * ((R + T) ** 3 - R ** 3)


def R_Mt(M, T, rho):
    return (
        -T + (T ** 2 - 4 * ((T ** 2) / 3 - M / (4 * Pi() * rho * T))) ** (1 / 2)
    ) / (2)


def t_RM(R, M, rho):
    return (M / ((4 / 3) * Pi() * rho) + R ** 3) ** (1 / 3) - R


def dtdR_RM(R, M, rho):
    return R ** 2 / (3 * M / (4 * Pi() * rho) + R ** 3) ** (2 / 3) - 1


# ' Composite function
def dPdR_RM(R, M, rho):
    return dPdR_Rt(R, t_RM(R, M, rho), rho) + dPdt_Rt(
        R, t_RM(R, M, rho), rho
    ) * dtdR_RM(R, M, rho)


# ' Functions based on (P,R,t) tripple
def P_Rt(R, T, rho):
    return (2.0 / 3) * Pi() * Gval() * (T * rho) ** 2 * (3 * R + T) / (R + T)


def dPdt_Rt(R, T, rho):
    return (
        (4.0 / 3)
        * rho ** 2
        * Pi()
        * Gval()
        * T
        * (3 * R ** 2 + 3 * R * T + T ** 2)
        / (R + T) ** 2
    )


def dPdR_Rt(R, T, rho):
    return 4 * T ** 3 * Gval() * Pi() * rho ** 2 / (3 * (R + T) ** 2)


def R_Pt(P, T, rho):
    return (
        (1.0 / 3)
        * T
        * (3 * P - 2 * rho ** 2 * Pi() * Gval() * T ** 2)
        / (-P + 2 * rho ** 2 * Pi() * Gval() * T ** 2)
    )


def t_RP(R, P, rho):
    t_RP = 1.366 * (P / (2 * Gval() * Pi())) ** (1.0 / 2) / rho
    n = 1
    while True:
        delta = -(P_Rt(R, t_RP, rho) - P) / dPdt_Rt(R, t_RP, rho)
        t_RP = t_RP + delta
        n = n + 1
        if abs(delta / t_RP) < 1e-06:
            break
        elif n > 20:
            t_RP = -2
            break

    return t_RP


# ' Functions based on the (P,R,M) tripple
def M_RP(R, P, rho):
    return M_Rt(R, t_RP(R, P, rho), rho)


def P_RM(R, M, rho):
    return P_Rt(R, t_RM(R, M, rho), rho)


def R_MP(M, P, rho):
    R_MP = (
        R_Mt(M, (P / (2 * Pi() * Gval())) ** (1 / 2) / rho, rho)
        - 0.5 * (P / (2 * Pi() * Gval())) ** (1 / 2) / rho
    )
    n = 1
    while True:
        delta = -(P_RM(R_MP, M, rho) - P) / dPdR_RM(R_MP, M, rho)
        R_MP = R_MP + delta
        n = n + 1
        if (
            abs(delta * rho / (P / (2 * Gval() * Pi()))) ** (1 / 2) < 1e-06
        ):  # Then    ' divide by est. value of t
            break
        elif n > 20:
            R_MP = -2
            break

    return R_MP


# ' root_abc used for a calculation related to tidal forces
def root_abc(a, b, c):
    root_abc = (b / a) ** (1 / 4)
    n = 1
    while True:
        delta = -(a * root_abc ** 4 - b + c * root_abc ** 3) / (
            4 * a * root_abc ** 3 + 3 * c * root_abc ** 2
        )
        root_abc = root_abc + delta
        n = n + 1
        if abs(delta / root_abc) < 1e-06:
            break
        elif n > 20:
            root_abc = -2
            break

    return root_abc


# ' Functions based on (P,S,R or t) tripple
def P_RS(R, S, rho):
    return (2.0 / 3) * Pi() * Gval() * rho ** 2 * (S - R) ** 2 * (S + 2 * R) / S


def dPdR_RS(R, S, rho):
    return 4 * Pi() * Gval() * rho ** 2 * R * (R - S) / S


def R_PS(P, S, rho):
    R_PS = 0.9 * S
    n = 1
    while True:
        delta = -(P_RS(R_PS, S, rho) - P) / dPdR_RS(R_PS, S, rho)
        R_PS = R_PS + delta
        n = n + 1
        if abs(delta / S) < 1e-06:
            break
        elif n > 20:
            R_PS = -2
            break

    return R_PS
