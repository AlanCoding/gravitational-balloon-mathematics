from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from transit_argument.config import CityConfig


OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
    "https://overpass.private.coffee/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]


def build_overpass_query(city: CityConfig, modes: tuple[str, ...] | None = None) -> str:
    south, west, north, east = city.bbox
    bbox = f"({south},{west},{north},{east})"
    route_modes = modes or city.route_modes
    mode_regex = "|".join(route_modes)
    return f"""
[out:json][timeout:180];
(
  relation["route"~"^({mode_regex})$"]{bbox};
);
out body center;
>;
out body center qt;
""".strip()


def _fetch_to_path(query: str, raw_path: Path, endpoint: str) -> None:
    payload = urllib.parse.urlencode({"data": query}).encode("utf-8")
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={"User-Agent": "transit-argument/0.1 (+local analysis pipeline)"},
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        raw_path.write_bytes(response.read())
    json.loads(raw_path.read_text(encoding="utf-8"))


def fetch_overpass(city: CityConfig, raw_path: Path, refresh: bool = False) -> Path:
    if raw_path.exists() and not refresh:
        return raw_path

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    last_error: Exception | None = None

    for endpoint in OVERPASS_ENDPOINTS:
        try:
            _fetch_to_path(build_overpass_query(city), raw_path, endpoint)
            return raw_path
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            time.sleep(2)

    combined: dict[tuple[str, int], dict[str, object]] = {}
    successful_modes = 0
    for mode in city.route_modes:
        fetched = False
        for endpoint in OVERPASS_ENDPOINTS:
            try:
                mode_path = raw_path.parent / f"overpass_{mode}.json"
                _fetch_to_path(build_overpass_query(city, modes=(mode,)), mode_path, endpoint)
                payload = json.loads(mode_path.read_text(encoding="utf-8"))
                for element in payload.get("elements", []):
                    combined[(str(element["type"]), int(element["id"]))] = element
                fetched = True
                successful_modes += 1
                break
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = exc
                time.sleep(2)
        if not fetched:
            continue

    if not combined or successful_modes == 0:
        raise RuntimeError(f"Failed to fetch Overpass data for {city.slug}: {last_error}")
    raw_path.write_text(json.dumps({"elements": list(combined.values())}), encoding="utf-8")
    return raw_path
