import math

# Constants that don't depend on the scenario
rho = 1.3
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
pi = math.pi
AU = 149597871000.
Skylab = 34400.
atm = 101325.
sun_mass = 1.989e+30
Stefan_const = 5.6704e-08



# https://en.wikipedia.org/wiki/BA_2100

# 65 to 70 tons
# 2,250 m^3
#
# 4/3*Pi*50^3
#
# 523598
