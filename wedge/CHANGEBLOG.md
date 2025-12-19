# Changeblog

## First coupled simulation

Here I tried to jump right to simulating with all 16 friction-buffers with the 250m radius reference design.

```
python multi_shell_time_sim.py
```

![First wrong simulation](short_journal/first_wrong_sim.png)

This is very unstable, the scenarios I did:
 - vanilla run, first stage went unstable
 - with a higher C_DAMP, the 5th stage or something went unstable

The image is of the 2nd one.

But none of this really matters, as specifically the `F_r` equation was made with the wrong assumptions.

Current high priority agenda items are:
 - correcting that `F_r` computation
 - Including the friction-buffer rotational speed in the simulation

The latter point will change us from 2 variables in each stage to 3.
This is necessary because it's almost certain that the final stages of the spiral are shooting
out the stage when there's actually no (or probably negative) relative velocity.
This is a highly stabilizing dynamical effect that can't be seen in the core equations,
although it remains very unclear whether this will change the overall outcome.

## Corrected for long-journal

To give a name to the previously mentioned `F_r` error, that used the **short-journal** assumption,
and we need the long-journal assumption to represent the axial symmetry.

Correct computation of `F_r` is quite complicated looking, but it seems to have worked in the end.
Here I got force values from the two components.
There is a major difference here than from the short-journal assumption,
which is that the two cross-over at a fairly low value.
In the short-journal assumption, the restoring `F_r` didn't become dominant until
maybe 2/3rd the channel width.

![Force values from fluid](long_journal/fr_and_ft.png)

Excitingly, the simulation in this current state can produce real output,
over a significant period of time.
This simulation was able to run for 1000 seconds of simulated time.

![x-axis movement of tubes](long_journal/trajectories_1000s.png)

Here we return again to the observation that `F_r` grows slower than `F_theta`
for small values of displacement. This is the primary driver of the wobble
you see throughout the simulation.

However, this still doesn't track change in angular velocity, which
has a mixed effect but is likely still restorative.

I'm fairly well convinced that this entire family of simulations
is going to produce an initial wobble about. These might
be sustainable and stable, but maybe not.
The next step is to definetely add the accounting for angular momentum.

As for broader implications, this still does not include turbulent flow.
I am very curious as to what implications that might have,
and this might forever be hard to simulate.

The lower cross-over point for the force ratios also has another tantalizing
implication - that a reasonable amount of intentional offset might work
completely to stabilize the construction.

## Including Angular Speeds

This turned out to not have much of an effect given the prior simulation.
But this is likely because of the relatively small displacements seen.

## Longer time runs

Those simulations so far ran 1,000s.
Over that time, relatively small displacements were seen.
This was good, but the small wobbles are concerning for longer-term operation,
as chance interactions over larger scales might still drive it unstable.

This time, I ran for 10,000s keeping everything else the same.
Here is the x position over time, the wobble & y position are
telling pretty much the same story.

![x overtime](10000s/x_time.png)

Key conclusions here:
 - the movement does reach a limit
 - shell that moves the most is 15, so the furthest out

This last point is intuitive and particularly interesting.
Because the transient started with a variation in position
of the inner-most shell.

You can also see no dampening, which is somewhat intended.
This model very much has no dampening in it on purpose.
If dampening was added, you might see them restore to
their original positions, but still unclear.

## Using a controlled displacement

The idea here is that we might "induce" the wedge effect intentionally.
This would be maintained by a constant force on the bearings of the tube,
pressed against a force maintained out the outermost stationary sheet.

ran:

```
python wedge/multi_shell_time_sim.py --hull-offset 30 --initial-perturb 0.1
```

Initial results are very weird, with the y value decreasing.

![y with control disp](control_disp/y_time.png)

Nothing interesting happened with the x position, and nothing could be
seen happening at all with the overall (x, y) plot because the starting
condition dwarfs any movement.

So to be sure, I tried it for the 10000 s run.
Wasn't enough, so I ran a 100,000 s run.
This finally revealed the end-state evolution of the system.

![y for long run](control_disp_hours/y_time.png)

The steady-state version of the system is in view now.
This state, also, is not oscillating.
That run was done with `--hull-offset 20`, meaing that
the hull is offset 30 meters in a tube surrounded by 100 meters
of friction buffers.

This result shows that that degree of offset **atains stability**,
which is an important result.

You might wonder, what is going on with these y values?
Weren't they supposed to be 0? And yes they were.
But this is probably a case of the simulation being right,
and me being wrong with how I formed the initial conditions.
I balanced the x values for the external force/offset.
But since there is also a tangential force obtained when
the rotor is offset, it's pretty easy to see how the final
solution might have some non-zero y values, and this is
what I believe we are getting.

## Pesimistic Radial force

Because the updated simulations for the long-journal approximations
have a fairly large `F_r` relative to `F_theta`, I didn't fully believe
the results.
So I added a "fudge" factor that would reduce the `F_r` value to a lower one.

![y for long run with Fr fudge](fr_fudge_02_long/x_time.png)

Compare to the [longer time runs](#longer-time-runs) section graph.
this is for the same time frame, differences are:

 - greater magnitude, 0.8 meter max, vs 0.4 meter
 - very arguably, shell 15 might still be increasing in magnitude

My present takeaway is that even if shell 15 is still increasing
its wobble size, that it's nowhere near driving unstable,
and doing so in the future is unlikely.

The channel widths are about 7 or 8 meters, so the wobbles are,
in fact, small, in both cases.

## Wrong F_r Angle

A major step backwards here - upon drawing force diagrams I realized
that my approach was wrong specifically in applying `F_r` along the
line of centers (the center of the rotor, center of the stator).

The simulation was updated, although the result is more pessimistic than
before. It is much harder to get a stable-looking simulation and now
only happens at the real extremes.
