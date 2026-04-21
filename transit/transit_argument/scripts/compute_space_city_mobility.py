from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from transit_argument.config import SPACE_CITY_ASSUMPTIONS, TABLE_DIR, THERMAL_ASSUMPTIONS
from transit_argument.io_utils import write_dataframe
from transit_argument.space_city import build_case, build_space_city_outputs, compute_atmosphere_channel_thermal


def main() -> None:
    atmosphere = build_case("atmosphere", SPACE_CITY_ASSUMPTIONS["atmosphere"])
    vacuum = build_case("vacuum", SPACE_CITY_ASSUMPTIONS["vacuum"])

    bucket_minutes = int(SPACE_CITY_ASSUMPTIONS["atmosphere"]["bucket_minutes"])
    max_bucket_minutes = int(SPACE_CITY_ASSUMPTIONS["atmosphere"]["max_bucket_minutes"])
    build_space_city_outputs([atmosphere, vacuum], bucket_minutes=bucket_minutes, max_bucket_minutes=max_bucket_minutes)
    channel_thermal = compute_atmosphere_channel_thermal(
        raw_case=SPACE_CITY_ASSUMPTIONS["atmosphere"],
        watts_per_person=float(THERMAL_ASSUMPTIONS["watts_per_person"]),
    )
    write_dataframe(TABLE_DIR / "space_city_atmosphere_channel_thermal.csv", channel_thermal)

    assumptions_rows = [
        {
            "category": "global",
            "name": "transfer_penalty_reference_min",
            "value": SPACE_CITY_ASSUMPTIONS["transfer_penalty_reference_min"],
            "notes": SPACE_CITY_ASSUMPTIONS["transfer_penalty_notes"],
        }
    ]
    for case_key in ["atmosphere", "vacuum"]:
        case = SPACE_CITY_ASSUMPTIONS[case_key]
        assumptions_rows.extend(
            [
                {"category": case_key, "name": "population", "value": case["population"], "notes": ""},
                {"category": case_key, "name": "people_per_node", "value": case["people_per_node"], "notes": ""},
                {"category": case_key, "name": "grid_shape", "value": "x".join(str(v) for v in case["grid_shape"]), "notes": ""},
                {"category": case_key, "name": "cell_spacing_m", "value": case["cell_spacing_m"], "notes": ""},
                {"category": case_key, "name": "access_time_min", "value": case["access_time_min"], "notes": ""},
                {"category": case_key, "name": "egress_time_min", "value": case["egress_time_min"], "notes": ""},
                {"category": case_key, "name": "transfer_time_min", "value": case["transfer_time_min"], "notes": ""},
            ]
        )
        if case_key == "atmosphere":
            for channel_key, channel_value in case["thermal_channel"].items():
                assumptions_rows.append(
                    {
                        "category": case_key,
                        "name": f"thermal_channel_{channel_key}",
                        "value": channel_value if not isinstance(channel_value, str) else "",
                        "notes": channel_value if isinstance(channel_value, str) else "",
                    }
                )
        if case_key == "vacuum":
            for pod_key, pod_value in case["pod"].items():
                assumptions_rows.append(
                    {
                        "category": case_key,
                        "name": f"pod_{pod_key}",
                        "value": pod_value if not isinstance(pod_value, str) else "",
                        "notes": pod_value if isinstance(pod_value, str) else "",
                    }
                )
    write_dataframe(TABLE_DIR / "space_city_mobility_assumptions.csv", pd.DataFrame(assumptions_rows))


if __name__ == "__main__":
    main()
