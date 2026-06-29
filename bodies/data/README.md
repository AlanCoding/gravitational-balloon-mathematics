# Data

The catalog is intentionally split into provenance layers:

- `origin/` for extracted or source-truth inputs
- `definition/` for curated body records with explicit source references
- `derived/` for generated catalogs, tables, and model outputs

The old `bodies_seed.csv` file is retained as an earlier staging artifact, but
the current canonical inputs are in the subdirectories above.
