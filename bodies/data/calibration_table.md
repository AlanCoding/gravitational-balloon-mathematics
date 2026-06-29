# Calibration Table

Pressure cap used here:

```text
P_max = 40 MPa
```

The temperature cap is ignored in this first check, so the accessible depth is
just the pressure-limited depth.

| Body | Gravity m/s^2 | Excavation rho kg/m^3 | Pressure depth km | Pressure depth mi | Regime |
| --- | ---: | ---: | ---: | ---: | --- |
| Earth | 9.82 | 2700 | 1.51 | 0.94 | pressure-limited |
| Moon | 1.62 | 3000 | 8.21 | 5.10 | pressure-limited |
| Mars | 3.73 | 3000 | 3.58 | 2.22 | pressure-limited |
| Ceres | 0.28 | 2162 | 65.17 | 40.50 | pressure-limited |
| Ganymede | 1.43 | 2000 | 14.03 | 8.72 | pressure-limited |
| Phobos | 0.01 | 1900 | 3756.65 | 2334.27 | radius-limited in practice |

The key pattern is what matters:

- big bodies still look shallow on a human scale
- small moons quickly become radius-limited before pressure is the issue
- the strip-mining visual should therefore flatten hard for the smallest bodies

