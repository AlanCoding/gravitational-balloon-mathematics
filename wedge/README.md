# Laminar Wedge Model for Multi-Shell Friction Buffers

This folder contains a first-pass, laminar lubrication model of the “friction buffer” stack around a 250 m radius rotating habitat tube. The goal is to quantify the **wedge effect** in a stack of nested cylinders and explore its static and dynamic behavior in the simplest possible framework.

The code is meant as a *toy model* that:

- Uses **short journal bearing** / Reynolds lubrication theory in the **laminar, incompressible, quasi-steady** limit.
- Treats each annular gap as a hydrodynamic “wedge” that generates pressure and forces when the inner and outer shells are offset.
- Scales up to a **17-shell stack** (16 gaps) with a fixed inner hull and fixed outer envelope, intermediate shells free to move in 2D.
- Lets us probe **static force–eccentricity behavior** and **time evolution** of shell positions under wedge forces and simple damping.

It is *not* a realistic CFD or rotor-dynamics model, but it captures some important qualitative features and exposes where the laminar wedge picture is misleading.

---

## Geometry and baseline parameters

The “reference” geometry is:

- Inner rotating habitat (the hull):
  - Radius: $`R_0 = 250\ \text{m}`$
  - Rim speed: $`V_\text{hull} \approx 50\ \text{m/s}`$
- Friction buffers:
  - 16 additional shells outside the hull → 17 shells total (indexed 0…16)
  - Nominal radial clearance per gap:  
    $`C_i \approx 6\ \text{m}`$ (currently uniform)
  - Axial length: $`L \approx 1000\ \text{m}`$ (same for all gaps in this toy model)
- Radii:
  - Shell $`i`$ inner radius:  
    $`R_i = R_0 + i\,C`$
- Fluid:
  - Air, dynamic viscosity $`\mu \approx 1.8\times10^{-5}\ \text{Pa·s}`$
  - Density $`\rho \approx 1.2\ \text{kg/m}^3`$

Shell 0 is the **hull**, shell 16 is the **outer stationary envelope**. In the multi-shell simulation, shells 1–15 can move in cross-section; 0 and 16 are fixed at the origin in (x, y).

The **shell speeds** are staged between hull and outer envelope. For now, the script uses a simple linear profile:

```math
v_i = V_\text{hull}\,\Bigl(1 - \frac{i}{N_\text{shells}-1}\Bigr),
```

so that the **relative linear speed** in each gap is (approximately) constant from hull to envelope.

---

## Single-gap laminar wedge model

Each gap between shell $`i`$ (inner) and shell $`i+1`$ (outer) is modeled as a short journal bearing with:

- Inner radius $`R_i`$,
- Clearance $`C_i`$,
- Axial length $`L`$,
- Relative surface speed across the gap $`U_\text{rel}`$ (from the staged velocities).

Let

- $`\mathbf{r}_i, \mathbf{r}_{i+1}`$ be the 2D center positions of the shells,
- $`\mathbf{d}_i = \mathbf{r}_i - \mathbf{r}_{i+1}`$ the relative displacement,
- $`e_i = \|\mathbf{d}_i\|`$ the eccentricity,
- $`c_i`$ the clearance of that gap,
- $`\varepsilon_i = e_i/c_i`$ the eccentricity ratio.

Under **short-bearing, laminar, incompressible, quasi-steady** Reynolds assumptions, the hydrodynamic reaction in that gap can be expressed in terms of:

```math
F_{r,i}(\varepsilon_i) = -F_{0,i}\, \frac{\varepsilon_i^2}{(1-\varepsilon_i^2)^2}, 
\qquad
F_{t,i}(\varepsilon_i) = +F_{0,i}\, \frac{\pi\,\varepsilon_i}{4(1-\varepsilon_i^2)^{3/2}},
```

with force scale

```math
F_{0,i} = \mu\, U_\text{rel}\,\frac{L^3}{c_i^2}.
```

Here:

- $`F_{r,i}`$ is the **radial** component (along the line of centers),
- $`F_{t,i}`$ is the **tangential / cross-coupled** component (90° ahead in the direction of rotation).

In vector form for gap $`i`$:

- Radial unit vector (inner → outer):  
  $`\hat{\mathbf{e}}_{r,i} = \mathbf{d}_i/e_i`$
- Tangential unit (rotate +90°):  
  $`\hat{\mathbf{e}}_{t,i} = (-\hat e_{r,i,y},\,\hat e_{r,i,x})`$

The fluid force on the **inner** shell from that gap is:

```math
\mathbf{F}_i^\text{(gap i)} = F_{r,i}\,\hat{\mathbf{e}}_{r,i} + F_{t,i}\,\hat{\mathbf{e}}_{t,i},
```

and on the **outer** shell: $`\mathbf{F}_{i+1}^\text{(gap i)} = -\mathbf{F}_i^\text{(gap i)}`$.

### Small-eccentricity behavior

For $`e \ll c`$, let $`\varepsilon \ll 1`$. Expand:

```math
F_r \approx -F_0\,\varepsilon^2 = -F_0\,\frac{e^2}{c^2}, 
\qquad
F_t \approx F_0\,\frac{\pi}{4}\,\varepsilon = F_0\,\frac{\pi}{4}\,\frac{e}{c}.
```

Key points:

- **Radial component** is **quadratic** in $`e`$: very weak near center.
- **Tangential component** is **linear** in $`e`$: dominant at small offsets.
- Their ratio near center:

```math
  \frac{|F_r|}{|F_t|} \approx \frac{4}{\pi}\,\frac{e}{c}.
```

So near $`e \approx 0`$ the wedge looks more like a **circulatory (cross-coupled) stiffness** than a nice radial spring.

### Where radial beats tangential

Solving $`|F_r| = |F_t|`$ for $`\varepsilon`$ gives

```math
\varepsilon_* \approx 0.618.
```

For the innermost gap with $`c = 6\ \text{m}`$, this is:

```math
e_* \approx 0.618 \times 6\ \text{m} \approx 3.7\ \text{m}.
```

So in this laminar model:

- For $`e \lesssim 0.6\,c`$, $`|F_t| > |F_r|`$ → tangential dominates.
- For $`e \gtrsim 0.6\,c`$, $`|F_r| > |F_t|`$ → radial becomes stronger.

---

## Multi-shell model

We assemble a 17-shell system where:

- Shell 0 (hull) and shell 16 (outer envelope) are **fixed** at the origin, $`(x,y)=(0,0)`$.
- Shells 1–15 are allowed to move in 2D.
- The total fluid force on shell $`s`$ is the sum of contributions from the inner and outer gaps:

```math
\mathbf{F}_s^\text{fluid}
= \mathbf{F}_s^\text{(gap s-1)} + \mathbf{F}_s^\text{(gap s)}.
```

The function:

- `total_fluid_forces(q, C, MU, U_rel, L)`

takes a global configuration vector

```math
q = [x_0,y_0,x_1,y_1,\dots,x_{16},y_{16}]
```

and returns the net fluid wedge force on each shell, automatically applying action–reaction between neighbors and inserting the laminar wedge law for each gap.

### Mass model for friction buffers

Each moving shell $`s \in \{1,\dots,15\}`$ is assigned a mass:

```math
m_s = \frac{1}{4}\,m_\text{air}^{\text{(inner annulus)}},
```

where

```math
m_\text{air}^{\text{(inner annulus i)}} 
= \rho\,\pi\,(R_{i+1}^2 - R_i^2)\,L.
```

This is a crude but concrete way to give the shells inertia on the same order as the air mass they “ride on,” while keeping the numbers manageable.

---

## Static force–eccentricity scripts

### `positional_250.py`

Defines:

- Geometry and fluid parameters,
- Single-gap wedge force functions:
  - `gap_force_magnitudes(e, c, mu, u_rel, L)`
  - `gap_force_vector(r_inner, r_outer, c, mu, u_rel, L)`
- Multi-shell assembly function:
  - `total_fluid_forces(q, C, MU, U_rel, L)`

Also includes a **stiffness matrix builder** using finite differences:

- `build_stiffness_matrix(q0, C, MU, U_rel, L, h=1e-4)`  
  returns $`K_{mn} = -\partial F_m/\partial q_n`$ evaluated at a configuration `q0`.

### `sim_250.py`

Sweeps the hull offset in the simplest configuration:

- Shell 0 (hull) displaced in +x by $`e`$,
- All other shells fixed at (0,0).

For each $`e`$, it computes the fluid force on the hull:

- $`F_x(e)`$ (radial),
- $`F_y(e)`$ (tangential),

and plots:

- $`F_r(e) = F_x(e)`$ and $`F_t(e) = F_y(e)`$,
- the force magnitude $`|\mathbf{F}(e)|`$,
- the ratio $`|F_r|/|F_t|`$.

These plots confirm:

- **Signs**: radial force on the offset hull is back toward the origin; tangential is 90° ahead.
- The **crossover** where $`|F_r| > |F_t|`$ appears near $`e \approx 3.7\ \text{m}`$ for a 6 m gap, matching the analytic formula.

---

## Dynamic simulations

### Hull-moving toy (discarded)

A first toy (`time_sim_250.py`) let the *hull* move under wedge forces with the outer shells fixed. This was useful to show:

- The laminar wedge’s **tangential force is linear in displacement** near the center.
- The **radial restoring force is quadratic**, so it’s invisible in a linear stability analysis at $`e\approx 0`$.
- With **no damping**, small perturbations evolve into **spiraling orbits** that grow in amplitude (unstable focus).

This behavior is **not** a bug: near $`e=0`$, the force field linearizes to

```math
\mathbf{F}(\mathbf{r}) \approx A\,J\,\mathbf{r},\quad
J=\begin{pmatrix}0&-1\\1&0\end{pmatrix},
```

a 90°-rotated spring that is linearly unstable when combined with inertia but no damping or direct restoring stiffness.

This model was then superseded by a more relevant one with the hull fixed and friction buffers moving.

### Multi-shell dynamics: moving buffers, fixed hull

The main dynamic script (`multi_shell_time_sim.py`) does:

- Fix hull (shell 0) and outer envelope (shell 16) at the origin.
- Give shells 1–15:
  - Masses as described above,
  - 2D positions and velocities $`(x_s,y_s,\dot x_s,\dot y_s)`$.
- Equations of motion:

```math
  m_s \ddot{\mathbf{r}}_s 
  = \mathbf{F}_s^\text{fluid}(\{\mathbf{r}_j\}) 
    - C_\text{damp}\,\dot{\mathbf{r}}_s,
```

  with **global scalar** damping $`C_\text{damp}`$ applied to each moving shell.

The simulation:

- Starts with a small offset of shell 1 (e.g., $`x_1 = 0.1\ \text{m}`$), all others concentric.
- Integrates forward in time with RK4.
- Stops with a useful error if any gap reaches $`e \ge c`$ (“shell hits the wall”), then plots the shells’ x(t), y(t), and orbits x–y up to that point.

#### Behavior observed

With $`C_\text{damp} = 0`$:

- Shell 1 (closest to hull) exhibits a **growing spiral** in x–y space — the unstable focus predicted by the linearized wedge field.
- Shell 2 moves a little; outer shells hardly move at all, because:
  - Coupling is weaker away from the initial perturbation,
  - Their masses are much larger.

With finite $`C_\text{damp} \sim 10^2–10^3\ \text{N·s/m}`$:

- The same general behavior persists (slow outward spirals) but slowed down.
- For larger $`C_\text{damp} \sim 10^3–10^4`$, the “most unstable” mode shape can shift outward (e.g. shell 5 hitting the wall first), reflecting:
  - Inhomogeneous masses,
  - Uniform damping per shell, and
  - The non-symmetric, cross-coupled nature of the wedge stiffness.

This is *qualitatively* similar to how real multi-rotor systems can move instability from one span to another when damping and stiffness are changed, but here it’s a feature of the very simplified model.

---

## Physical interpretation and limitations

### Key theoretical points

1. **Static wedge support vs. centering**  
   - The laminar wedge can produce a large **radial load capacity** at finite eccentricity $`e \sim 0.7\,c`$.  
   - Near $`e=0`$, the radial component is too weak (∝ $`e^2`$) to act as a strong centering mechanism.
   - The laminar wedge alone therefore **does not “like” to maintain centerline**; real hydrodynamic bearings operate deliberately off-center under load.

2. **Dynamic instability with cross-coupling**  
   - The leading-order force near center is tangential (∝ displacement) and acts like a **circulatory stiffness**.  
   - Combined with inertia and no damping, this gives a **linearly unstable focus** — trajectories spiral out.
   - Real bearings avoid runaway by:
     - Operating at finite eccentricity under load,
     - Having **film damping** from unsteady Reynolds physics,
     - Including structural stiffness and damping.

3. **Friction buffers are not self-centering in this laminar model**  
   - With symmetric geometry and no external load, the friction buffers naturally sit in the **small-e regime** where the laminar wedge offers weak radial support.  
   - In this regime, the toy model predicts orbiting / drifting rather than robust centering, unless strong structural constraints and/or realistic damping are added.

### Model limitations

- **Laminar, quasi-steady Reynolds**:
  - Ignores turbulence (very likely present at the actual Reynolds numbers).
  - Ignores unsteady terms that produce *velocity-dependent* film forces (true damping).
- **Short-bearing approximation**:
  - Treats each gap as a short journal bearing; end leakage and full 3D effects are not modeled.
- **Ad-hoc damping**:
  - `C_damp` is a crude global isotropic damper per shell, not a proper fluid dynamic coefficient matrix.
- **No structural elements yet**:
  - There are no springs / tethers / balloon ribs modeled; in any realistic friction-buffer design, those are essential.

---

## How to run

Assuming you’re in the repo root:

```bash
cd wedge

# Static force–eccentricity sanity check (single-hull offset vs 16 fixed shells)
python sim_250.py

# Multi-shell dynamic simulation: friction buffers moving, hull & outer shell fixed
python multi_shell_time_sim.py

