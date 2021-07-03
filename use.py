from gb.inflation import t_RP
from gb.old import inflation as old_inflation


print('value from revised methods')
print(t_RP(12.0e3, 1.0e5))

print('')
print('value from old methods')
print(old_inflation.t_RP(12.0e3, 1.0e5, 1.3))
