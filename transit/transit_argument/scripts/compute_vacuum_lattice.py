from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transit_argument.config import LATTICE_ASSUMPTIONS, TABLE_DIR
from transit_argument.io_utils import write_dataframe
from transit_argument.thermal import compute_lattice_summary


def main() -> None:
    sky_frame, summary_frame = compute_lattice_summary(
        population=int(LATTICE_ASSUMPTIONS["population"]),
        people_per_habitat=int(LATTICE_ASSUMPTIONS["people_per_habitat"]),
        watts_per_person=float(LATTICE_ASSUMPTIONS["watts_per_person"]),
        habitat_radius_m=float(LATTICE_ASSUMPTIONS["habitat_radius_m"]),
        spacing_values_m=list(LATTICE_ASSUMPTIONS["spacing_values_m"]),
        surface_samples=int(LATTICE_ASSUMPTIONS["surface_samples"]),
        direction_samples=int(LATTICE_ASSUMPTIONS["direction_samples"]),
        neighbor_shell=int(LATTICE_ASSUMPTIONS["neighbor_shell"]),
        sky_fraction_threshold=float(LATTICE_ASSUMPTIONS["sky_fraction_threshold"]),
        radiator_temperature_k=float(LATTICE_ASSUMPTIONS["radiator_temperature_k"]),
        sigma=float(LATTICE_ASSUMPTIONS["stefan_boltzmann_constant"]),
        background_temperature_k=float(LATTICE_ASSUMPTIONS["background_temperature_k"]),
    )
    write_dataframe(TABLE_DIR / "vacuum_lattice_sky_fraction_vs_spacing.csv", sky_frame)
    write_dataframe(TABLE_DIR / "vacuum_lattice_thermal_summary.csv", summary_frame)


if __name__ == "__main__":
    main()
