from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    python = sys.executable
    for script in [
        "scripts/run_transit.py",
        "scripts/compute_thermal_bounds.py",
        "scripts/compute_vacuum_lattice.py",
        "scripts/build_project_summary.py",
    ]:
        subprocess.run([python, str(ROOT / script)], check=True)


if __name__ == "__main__":
    main()
