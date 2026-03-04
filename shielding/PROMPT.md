This folder should host a Monte Carlo simulation for shielding calculations.

In both cases, we want to generate a ray of radiation on the "space" side of the shielding.
This will be random in position (doesn't matter for reference) and angle.
The position only needs to be random within the periodic unit, because it is infinetely repeating.
So if we have $p$, repeating pitch, the position could be selected anywhere 0-p randomly to
be an accurate sampling.

The radiation angle should be isotropic.

### Description of Reference

We have a solid wall of shielding.
This is an infite wall.
Space is on one side, and interior of a habitat with humans to shield from radiation is on the other side.
Rays are generated on the space side of the wall.
Angles of the rays of radiation are evenly distributed over the full 180 degrees that the wall is exposed to.
The shielding is a constant depth d.
The representative optical depth for this length of shielding is:

$  \tau = \lambda d \approx 5  $.

Isotropic-hemisphere average transmission for the flat wall (standard radiation-transport result):

$$\langle T_{\text{flat}} \rangle = 2 \int_0^1 \mu \, e^{-\tau / \mu} \, d\mu$$

This results in a value of $  \langle T_{\text{flat}} \rangle \approx 0.0018  $, which is specific to our
number of 5.

This represents the baseline of shielding quality we have to acheive.

You should apply your Monte Carlo simulation to this reference scenario as a sanity check

### Chevron Shielding

**Connected Chevron Shielding Geometry**  
**(Infinite Repeating 2D Pattern – Monte Carlo Input Specification)**  

**Coordinate System**  
- \( x \): thickness direction, \( 0 \leq x \leq L \) (space side at \( x = 0 \), habitat side at \( x = L \))  
- \( z \): lateral direction (periodic with period \( p \))  
- \( y \): infinite extrusion direction (fully translationally invariant)  

**Infinite-Wall Assumption**  
The geometry is an infinite slab, periodic in \( z \) with period \( p \), and extruded infinitely in \( y \). Use periodic boundary conditions in \( z \) (or replicate the unit cell) for the Monte Carlo domain.

**Parameters**
- \( \theta = 45^\circ \) (blade angle from the \( x \)-axis)  
- \( t \): blade thickness measured perpendicular to the blade surface  
- \( p \): repeating pitch in the \( z \)-direction  
**Key design constraint**: \( t \ll p \) and \( t \ll L \) (thin-blade limit, typically \( t/p \approx 0.02\)–\(0.05\) for ~40 % free-flow area)

**Centerline Path of One Chevron Blade** (reference unit, \( z_\text{offset} = 0 \))  
The centerline is piecewise linear:  

1. Ascending segment (\( 0 \leq x \leq L/2 \)):  
   \[ z_1(x) = x \cdot \tan\theta \]  

2. Descending segment (\( L/2 \leq x \leq L \)):  
   \[ z_2(x) = L \cdot \tan\theta - x \cdot \tan\theta \]  

**Full Repeating Pattern**  
Centerlines for all units:  
\[ z_c(x) = z_1(x)\ \text{or}\ z_2(x) + k \cdot p \qquad (k \in \mathbb{Z}) \]  

**Material Region**  
A point \( (x, y, z) \) is inside shielding material if its perpendicular distance to the nearest centerline segment (accounting for all periodic images in \( z \)) satisfies  
\[ d_\perp(x, z) \leq t/2 \]  

**Implementation Notes for Monte Carlo**  
- Worst-case path length through material = \( t \) (normal incidence on any blade segment).  
- Every straight-line trajectory from \( x = 0 \) to \( x = L \) intersects at least one blade (zero line-of-sight tunnels).  
- Air channels are fully connected and serpentine between adjacent chevrons.  
- In code (Geant4, MCNP, FLUKA, etc.): define as union of thick slanted parallelograms (or use distance-to-polyline function) with periodic replication in \( z \).  

Objectively, the simulation should find a $T_{\text{flat}}$ value for this geometry.

