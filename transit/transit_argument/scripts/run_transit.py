from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transit_argument.config import CITIES, DIAGNOSTIC_DIR, GEOJSON_DIR, RAW_DIR, TABLE_DIR
from transit_argument.io_utils import write_dataframe
from transit_argument.transit_model import run_city


def main() -> None:
    parser = argparse.ArgumentParser(description="Run transit reachability analysis")
    parser.add_argument("--city", action="append", dest="cities", help="City slug to run; can be repeated")
    parser.add_argument("--refresh", action="store_true", help="Refresh raw cached downloads")
    args = parser.parse_args()

    city_keys = args.cities or list(CITIES.keys())
    summaries = []
    for city_key in city_keys:
        if city_key not in CITIES:
            raise SystemExit(f"Unknown city slug: {city_key}")
        summaries.append(
            run_city(
                city=CITIES[city_key],
                raw_root=RAW_DIR,
                table_root=TABLE_DIR,
                diagnostics_root=DIAGNOSTIC_DIR,
                geojson_root=GEOJSON_DIR,
                refresh=args.refresh,
            )
        )

    summary_frame = pd.DataFrame(summaries).sort_values("city")
    write_dataframe(TABLE_DIR / "transit_run_summary.csv", summary_frame)


if __name__ == "__main__":
    main()
