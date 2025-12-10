Perfect, let’s lock in a clean version of the forces with everything named and all assumptions spelled out.

---

## Geometry & variables

* $R$ — journal (rotor) radius
* $R + c$ — bearing inner radius
* $c$ — radial clearance, with $c \ll R$ (thin film)
* $L$ — bearing (axial) length
* $e$ — eccentricity (displacement of journal center from bearing center)
* $\varepsilon = e / c$ — eccentricity ratio ($0 \le \varepsilon < 1$)
* $\theta$ — circumferential angle, measured from the line of minimum film thickness (aligned with the displacement $e$)
* $\mu$ — dynamic viscosity of the fluid
* $\omega$ — angular speed of the journal
* $U = \omega R$ — surface speed of the journal
* Film thickness:

  $$
  h(\theta) = c\,(1 + \varepsilon \cos\theta)
  $$

* $p(\theta)$ — hydrodynamic pressure in the fluid film at angle $\theta$
* Coordinates:

  * $x$-axis along the eccentricity vector (journal displaced in $+x$)
  * $y$-axis 90° ahead in rotation sense
  * “Radial” direction = along $\pm \hat{x}$
  * “Tangential” direction = along $\pm \hat{y}$

---

## Reynolds equation (long, laminar journal)

In the “infinitely long” journal-bearing model (no axial variation), the Reynolds equation reduces to a 1D ODE in $\theta$:

$$
\frac{d}{d\theta}
\left(
h(\theta)^3 \frac{dp}{d\theta}
\right)
=
6\,\mu\,\omega\,R^2\,\frac{dh}{d\theta}.
\tag{Reynolds}
$$

with $h(\theta) = c(1+\varepsilon\cos\theta)$ and $p(\theta)$ taken $2\pi$-periodic (Sommerfeld full-film assumption).

You solve this ODE (analytically or numerically) to get $p(\theta)$.

---

## Radial restoring force $F_r$

Pressure acts normal to the journal surface. The elemental pressure force on area $dA = R L\,d\theta$ is

$$
d\vec{F}_p = -p(\theta)\,(\cos\theta\,\hat{x} + \sin\theta\,\hat{y})\,R L\,d\theta.
$$

Integrate around the circumference:

$$
F_x = -R L \int_0^{2\pi} p(\theta)\cos\theta\,d\theta,
\qquad
F_y = -R L \int_0^{2\pi} p(\theta)\sin\theta\,d\theta.
$$

Choosing “radial” direction along $+\hat{x}$, the **radial restoring force** (pointing opposite the displacement) is:

$$
F_r \equiv -F_x
=
R L \int_0^{2\pi} p(\theta)\cos\theta\,d\theta.
$$

* Direction: opposite the displacement $e$ (i.e. from journal center back toward bearing center).
* For small $\varepsilon$, this behaves like a spring: $F_r \approx -k\,e$, where $k$ comes from the $\varepsilon$-dependence of $p(\theta)$.

---

## Assumptions

All of the above rests on these assumptions:

* **Geometry**

  * Circular journal of radius $R$ inside a circular bearing of radius $R+c$, constant clearance $c$.
  * Journal axis and bearing axis are parallel; no tilt or misalignment.
  * Journal center displaced by $e$ in a fixed direction (steady eccentricity).
  * Film thickness purely circumferential: $h(\theta) = c(1+\varepsilon\cos\theta)$.
  * Thin film: $c \ll R$.

* **Kinematics**

  * Journal rotates at constant angular speed $\omega$.
  * Bearing is stationary in the chosen frame.
  * Steady-state conditions: no time dependence in $h$ or $p$ (no squeeze or startup effects).

* **Fluid properties**

  * Newtonian fluid.
  * Incompressible.
  * Constant viscosity (isoviscous): $\mu$ does not depend on $p$ or $T$.

* **Flow regime & lubrication theory**

  * Laminar flow in the film; inertia terms neglected (creeping-flow / Stokes regime in the gap).
  * Lubrication approximation:

    * Film is thin: variations across the gap dominate; curvature across the film is negligible.
    * Pressure is uniform across the film thickness.
    * Velocity profile across the gap is approximately linear (Couette + Poiseuille).

* **Bearing model (“infinitely long” / Sommerfeld)**

  * No axial variation: $\partial p/\partial z = 0$ (pressure depends only on $\theta$).
  * Side leakage is neglected (effectively infinite length, or perfectly uniform in $z$).

* **Film & boundary conditions**

  * Fully flooded: lubricant continuously supplied, no starvation.
  * No cavitation: pressure is allowed to go below ambient; a single continuous film wraps full $0 \to 2\pi$.
  * Periodic pressure: $p(\theta+2\pi) = p(\theta)$.

* **For the simple $F_\theta$ formula**

  * Dominant tangential force comes from viscous shear at the journal.
  * Pressure-induced tangential component $F_{\theta,\text{press}}$ is neglected (or treated as a small correction).
  * End effects and 3D secondary flows are neglected.

If you’re happy with this as the “definition” of the wedge-effect forces, the next natural step (if you want) is: pick numbers for $R$, $c$, $\mu$, $\omega$, $L$, choose a few $\varepsilon$, and actually evaluate $F_r$ numerically from Reynolds + the integral, and compare it to $F_\theta$ to see how stiff the wedge really is in your air-annulus regime.
