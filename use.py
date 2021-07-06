from gb import inflation as new_inflation
from gb.ported import gravity as old_inflation

from math import pi

import matplotlib.pyplot as plt


print('value from revised methods')
print(new_inflation.t_RP(12.0e3, 1.0e5))

print('')
print('value from old methods')
print(old_inflation.t_RP(12.0e3, 1.0e5, 1.3))


print('')
print('functions that still need to be implemented:')
for name in set(dir(old_inflation)) - set(dir(new_inflation)):
    print('  ' + str(name))


M = 1.e10
N_points = 200

R0 = (M * 3. / (4. * pi))**(1./3.)

R_values = [(2. / N_points) * i * R0 for i in range(N_points + 1)]

P_values = [new_inflation.P_RM(R, M) / new_inflation.P_RM(0., M) for R in R_values]

plt.plot(R_values, P_values)
plt.title('Pressure vs. Inner Radius, constant Mass')
plt.ylabel('P relative to original core P')
plt.xlabel('Radius relative to asteroid radius')
plt.savefig('P_vs_r.png')

V_values = [(4./3.)*pi*R**3 for R in R_values]

plt.plot(V_values, P_values)
plt.title('Volume vs. Inner Radius, constant Mass')
plt.ylabel('P relative to original core P')
plt.xlabel('Volume relative to asteroid rock volume')
plt.savefig('P_vs_V.png')
