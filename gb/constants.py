# Constants that don't depend on the scenario
rho = 1.3 * 1000.
g = 9.8

Cd_streamlined = 0.04

# Experiment scaling
# 	mu	rho
# 	Pa-s	kg/m3
# air	1.98E-05	1.3
# water	1.00E-03	1.00E+03
# glycerol	1.412	1.00E+03
# He	1.87E-05	0.169
# Acetone	3.16E-04	791
# Methanol	5.60E-04	801

Gval = 6.67384e-11
AU = 149597871000.
Skylab = 34400.
atm = 101325.
Stefan_const = 5.6704e-08

example_masses = dict(
    # sun=1.989e30,
    # earth=5972.e24,
    # moon=73.46e24,
    ceres=0.938e24,
    vesta=2.590e20,
    pallas=204.e18,
    hygiea=83.e18,
    psyche=24.e18,
    phobos=1.0659e16
)


# https://en.wikipedia.org/wiki/BA_2100

# 65 to 70 tons
# 2,250 m^3
#
# 4/3*Pi*50^3
#
# 523598

# # Reference Values
# r1 = 250
# r2 = 350
# delta = 100
