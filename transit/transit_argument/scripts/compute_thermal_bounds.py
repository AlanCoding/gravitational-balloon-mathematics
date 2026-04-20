from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transit_argument.config import TABLE_DIR, THERMAL_ASSUMPTIONS
from transit_argument.io_utils import write_dataframe
from transit_argument.thermal import compute_sphere_thermal_bounds


def main() -> None:
    frame = compute_sphere_thermal_bounds(
        population=int(THERMAL_ASSUMPTIONS["population"]),
        watts_per_person=float(THERMAL_ASSUMPTIONS["watts_per_person"]),
        surface_temperatures_k=list(THERMAL_ASSUMPTIONS["surface_temperatures_k"]),
        sigma=float(THERMAL_ASSUMPTIONS["stefan_boltzmann_constant"]),
        background_temperature_k=float(THERMAL_ASSUMPTIONS["background_temperature_k"]),
    )
    write_dataframe(TABLE_DIR / "macrohabitat_sphere_thermal_bounds.csv", frame)


if __name__ == "__main__":
    main()
