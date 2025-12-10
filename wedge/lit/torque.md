# Equations for Torque Including Displacement

The simulation here is currently aiming to be 3-variable for each friction-buffer

 - center position, alternatively $(x, y)$
   - $r$ value
   - $\theta$ value
 - angular speed of the given stage

The equations here should give an accurate torque for a given stage,
for influence from a single neighbor (each stage has 2 neighbors).

This torque will then be used in the angular momentum balance equation,
which will ultimately give the 2nd derivative of angular position.
We do not care about angular position due to symmetry,
so only angular speed is tracked.

The time-domain evolution of angular speed is unblocked by having this equation.

## Geometry and setup

* Inner cylinder (rotor) radius: $R_1$
* Outer cylinder (stator) radius: $R_2$
* Gap thickness (concentric case):

  $$
  \delta \equiv R_2 - R_1 \quad\text{with}\quad \delta \ll R_1
  $$

* Inner cylinder angular speed: $\Omega$
* Tangential speed at rotor surface:

  $$
  U = \Omega R_1
  $$

* Dynamic viscosity: $\mu$
* Eccentricity (offset of inner cylinder from center): $e$
* Dimensionless eccentricity:

  $$
  \varepsilon \equiv \frac{e}{\delta}, \quad 0 \le \varepsilon < 1
  $$

In the lubrication / narrow-gap picture, the local film thickness as a function of azimuthal angle $\theta$ is

$$
h(\theta) = \delta\bigl(1 + \varepsilon \cos\theta\bigr).
$$

---

## Baseline torque (concentric case)

For concentric cylinders with a narrow gap, the laminar Couette torque per unit length on the inner cylinder is

$$
T_0' \approx \frac{2\pi \mu \Omega R_1^3}{\delta}.
$$

(This is the narrow-gap limit of the exact Taylor–Couette result.)

---

## Modified torque with eccentricity

Using the small-gap / lubrication approximation and treating the local flow as Couette shear with gap $h(\theta)$, the torque per unit length on the eccentric rotor is

$$
T'(\varepsilon)
= \mu U R_1^2 \int_0^{2\pi} \frac{d\theta}{h(\theta)}
= \frac{\mu U R_1^2}{\delta} \int_0^{2\pi} \frac{d\theta}{1 + \varepsilon\cos\theta}.
$$

The standard integral

$$
\int_0^{2\pi} \frac{d\theta}{1 + \varepsilon\cos\theta}
= \frac{2\pi}{\sqrt{1 - \varepsilon^2}}
\quad (|\varepsilon| < 1)
$$

gives the final closed form:

$$
\boxed{
T'(\varepsilon)
= \frac{2\pi \mu \Omega R_1^3}{\delta}\,\frac{1}{\sqrt{1 - \varepsilon^2}}
= \frac{T_0'}{\sqrt{1 - \varepsilon^2}},
\quad \varepsilon = \frac{e}{\delta}.
}
$$

This is the retarding torque magnitude in steady laminar flow for a slightly (or strongly) eccentric inner rotor, under the same assumptions as the concentric Taylor–Couette case plus the narrow-gap/lubrication approximation.
