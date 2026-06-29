# Origin Data

This directory holds source-of-truth inputs.

Contents should be treated as authoritative inputs, not derived outputs:

- `sources.csv` records where each body source came from
- `orbital_elements.csv` stores orbit definitions used for the delta-v proxy
- `asteroids_dastcom5_reference.csv` is extracted directly from the local JPL DASTCOM5 dump

These files may be combined later, but they should remain separate from the
curated definition and derived catalog layers.
