# Changeblog

## First coupled simulation

Here I tried to jump right to simulating with all 16 friction-buffers with the 250m radius reference design.

```
python multi_shell_time_sim.py
```

![First wrong simulation](first_wrong_sim.png)

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
