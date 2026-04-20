from __future__ import annotations

import heapq
import math
import re
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from transit_argument.config import CityConfig
from transit_argument.geo import haversine_m
from transit_argument.io_utils import read_json, write_dataframe, write_json
from transit_argument.overpass import fetch_overpass


STATION_TAGS = {"station", "stop_position", "platform"}
MODE_SPEED_DEFAULT = {"subway": 34.0, "light_rail": 28.0, "monorail": 32.0, "train": 42.0}


@dataclass(frozen=True)
class Station:
    station_id: str
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Segment:
    from_station: str
    to_station: str
    line_id: str
    line_name: str
    mode: str
    travel_time_min: float


def normalize_name(name: str) -> str:
    lowered = name.casefold()
    lowered = lowered.replace("st.", "st").replace("saint-", "saint ")
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def _element_coord(element: dict[str, object]) -> tuple[float, float] | None:
    if "lat" in element and "lon" in element:
        return float(element["lat"]), float(element["lon"])
    center = element.get("center")
    if isinstance(center, dict) and "lat" in center and "lon" in center:
        return float(center["lat"]), float(center["lon"])
    return None


def _station_like(tags: dict[str, str]) -> bool:
    railway = tags.get("railway", "")
    public_transport = tags.get("public_transport", "")
    station = tags.get("station", "")
    return railway in {"station", "halt", "tram_stop"} or public_transport in STATION_TAGS or station in {
        "subway",
        "light_rail",
        "train",
        "monorail",
    }


def _dedupe_station_key(name: str, lat: float, lon: float) -> str:
    return f"{normalize_name(name)}::{round(lat, 4)}::{round(lon, 4)}"


def _extract_network(overpass_payload: dict[str, object], city: CityConfig) -> tuple[dict[str, Station], list[Segment], dict[str, list[str]]]:
    elements = overpass_payload["elements"]
    by_key: dict[tuple[str, int], dict[str, object]] = {}
    for element in elements:
        by_key[(str(element["type"]), int(element["id"]))] = element

    station_ids_by_element: dict[tuple[str, int], str] = {}
    stations: dict[str, Station] = {}

    for element in elements:
        tags = element.get("tags")
        if not isinstance(tags, dict) or "name" not in tags:
            continue
        if not _station_like(tags):
            continue
        coords = _element_coord(element)
        if coords is None:
            continue
        lat, lon = coords
        station_key = _dedupe_station_key(str(tags["name"]), lat, lon)
        if station_key not in stations:
            stations[station_key] = Station(
                station_id=station_key,
                name=str(tags["name"]),
                lat=lat,
                lon=lon,
            )
        station_ids_by_element[(str(element["type"]), int(element["id"]))] = station_key

    segments: list[Segment] = []
    lines_by_station: dict[str, list[str]] = {station_id: [] for station_id in stations}

    for element in elements:
        tags = element.get("tags")
        if not isinstance(tags, dict):
            continue
        mode = tags.get("route")
        if mode not in MODE_SPEED_DEFAULT:
            continue

        line_name = str(tags.get("name", tags.get("ref", f"{mode}-{element['id']}")))
        line_id = f"{mode}:{element['id']}"
        member_station_ids: list[str] = []

        for member in element.get("members", []):
            if not isinstance(member, dict):
                continue
            member_key = (str(member.get("type")), int(member.get("ref", -1)))
            role = str(member.get("role", ""))
            station_id = station_ids_by_element.get(member_key)
            if station_id is None and role in {"stop", "platform", "station", "stop_entry_only", "stop_exit_only", ""}:
                member_element = by_key.get(member_key)
                if member_element is not None:
                    member_tags = member_element.get("tags")
                    if isinstance(member_tags, dict) and "name" in member_tags and _station_like(member_tags):
                        coords = _element_coord(member_element)
                        if coords is not None:
                            station_id = _dedupe_station_key(str(member_tags["name"]), coords[0], coords[1])
            if station_id is None:
                continue
            if member_station_ids and member_station_ids[-1] == station_id:
                continue
            member_station_ids.append(station_id)

        if len(member_station_ids) < 2:
            continue

        speed_kmh = city.speed_overrides_kmh.get(mode, MODE_SPEED_DEFAULT[mode])
        for from_station, to_station in zip(member_station_ids, member_station_ids[1:]):
            if from_station == to_station:
                continue
            left = stations[from_station]
            right = stations[to_station]
            distance_m = haversine_m(left.lat, left.lon, right.lat, right.lon)
            if distance_m < 120.0 or distance_m > 20_000.0:
                continue
            travel_time = (distance_m / 1000.0) / speed_kmh * 60.0 + city.dwell_time_min
            segments.append(
                Segment(
                    from_station=from_station,
                    to_station=to_station,
                    line_id=line_id,
                    line_name=line_name,
                    mode=mode,
                    travel_time_min=travel_time,
                )
            )
            segments.append(
                Segment(
                    from_station=to_station,
                    to_station=from_station,
                    line_id=line_id,
                    line_name=line_name,
                    mode=mode,
                    travel_time_min=travel_time,
                )
            )
            lines_by_station[from_station].append(line_id)
            lines_by_station[to_station].append(line_id)

    return stations, segments, lines_by_station


def _add_walking_segments(city: CityConfig, stations: dict[str, Station], segments: list[Segment]) -> list[Segment]:
    station_list = list(stations.values())
    max_distance = city.max_walking_link_m
    for index, left in enumerate(station_list):
        for right in station_list[index + 1 :]:
            distance_m = haversine_m(left.lat, left.lon, right.lat, right.lon)
            if distance_m > max_distance:
                continue
            walk_time = (distance_m / 1000.0) / city.walking_speed_kmh * 60.0
            line_id = f"walk:{left.station_id}:{right.station_id}"
            segments.append(
                Segment(
                    from_station=left.station_id,
                    to_station=right.station_id,
                    line_id=line_id,
                    line_name="walk",
                    mode="walk",
                    travel_time_min=walk_time,
                )
            )
            segments.append(
                Segment(
                    from_station=right.station_id,
                    to_station=left.station_id,
                    line_id=line_id,
                    line_name="walk",
                    mode="walk",
                    travel_time_min=walk_time,
                )
            )
    return segments


def _select_anchors(city: CityConfig, stations: dict[str, Station]) -> list[str]:
    norm_index: dict[str, list[str]] = {}
    for station_id, station in stations.items():
        norm_index.setdefault(normalize_name(station.name), []).append(station_id)

    selected: list[str] = []
    for candidate in city.anchor_candidates:
        candidate_norm = normalize_name(candidate)
        direct = norm_index.get(candidate_norm, [])
        if direct:
            selected.append(direct[0])
            continue
        partial_matches: list[tuple[float, str]] = []
        for station_id, station in stations.items():
            station_norm = normalize_name(station.name)
            if candidate_norm in station_norm or station_norm in candidate_norm:
                partial_matches.append((haversine_m(city.center[0], city.center[1], station.lat, station.lon), station_id))
        if partial_matches:
            partial_matches.sort()
            selected.append(partial_matches[0][1])

    if selected:
        return list(dict.fromkeys(selected))

    fallback = sorted(
        stations.values(),
        key=lambda station: haversine_m(city.center[0], city.center[1], station.lat, station.lon),
    )
    return [station.station_id for station in fallback[:3]]


def _run_anchor_dijkstra(
    city: CityConfig,
    anchor_station: str,
    stations: dict[str, Station],
    segments: list[Segment],
) -> tuple[dict[str, float], dict[str, int]]:
    adjacency: dict[str, list[Segment]] = {}
    for segment in segments:
        adjacency.setdefault(segment.from_station, []).append(segment)

    counter = 0
    queue: list[tuple[float, int, str, str | None, int]] = [(city.entry_penalty_min, counter, anchor_station, None, 0)]
    best_state: dict[tuple[str, str | None], tuple[float, int]] = {(anchor_station, None): (city.entry_penalty_min, 0)}
    best_station_time: dict[str, float] = {anchor_station: city.entry_penalty_min}
    best_station_transfers: dict[str, int] = {anchor_station: 0}

    while queue:
        current_time, _, station_id, current_line, transfers = heapq.heappop(queue)
        state_key = (station_id, current_line)
        state_value = best_state.get(state_key)
        if state_value is None or current_time > state_value[0] + 1e-9:
            continue

        for segment in adjacency.get(station_id, []):
            next_line = None if segment.mode == "walk" else segment.line_id
            transfer_penalty = 0.0
            next_transfers = transfers
            if current_line is not None and next_line is not None and current_line != next_line:
                transfer_penalty = city.transfer_penalty_min
                next_transfers += 1
            candidate_time = current_time + segment.travel_time_min + transfer_penalty
            next_state = (segment.to_station, next_line)
            previous = best_state.get(next_state)
            if previous is None or candidate_time < previous[0] - 1e-9 or (
                abs(candidate_time - previous[0]) <= 1e-9 and next_transfers < previous[1]
            ):
                best_state[next_state] = (candidate_time, next_transfers)
                counter += 1
                heapq.heappush(queue, (candidate_time, counter, segment.to_station, next_line, next_transfers))
                final_time = candidate_time + city.exit_penalty_min
                best_time = best_station_time.get(segment.to_station)
                best_transfer = best_station_transfers.get(segment.to_station, math.inf)
                if best_time is None or final_time < best_time - 1e-9 or (
                    abs(final_time - best_time) <= 1e-9 and next_transfers < best_transfer
                ):
                    best_station_time[segment.to_station] = final_time
                    best_station_transfers[segment.to_station] = next_transfers

    return best_station_time, best_station_transfers


def _build_population_assignment(city: CityConfig, stations: dict[str, Station]) -> tuple[pd.DataFrame, pd.DataFrame]:
    south, west, north, east = city.bbox
    lat_step = 0.01
    lon_step = 0.01
    rows: list[dict[str, object]] = []
    station_population: dict[str, float] = {station_id: 0.0 for station_id in stations}
    kernel_scale_m = city.density_kernel_km * 1000.0
    max_assign_m = city.catchment_radius_km * 1000.0

    lat = south
    while lat <= north + 1e-9:
        lon = west
        while lon <= east + 1e-9:
            nearest_station: str | None = None
            nearest_distance = math.inf
            kernel_sum = 0.0
            for station_id, station in stations.items():
                distance = haversine_m(lat, lon, station.lat, station.lon)
                if distance < nearest_distance:
                    nearest_station = station_id
                    nearest_distance = distance
                kernel_sum += math.exp(-0.5 * (distance / kernel_scale_m) ** 2)

            center_distance = haversine_m(lat, lon, city.center[0], city.center[1])
            center_weight = 0.6 + 0.4 * math.exp(-0.5 * (center_distance / 10_000.0) ** 2)
            weight = kernel_sum * center_weight
            assigned = nearest_station if nearest_distance <= max_assign_m else None
            rows.append(
                {
                    "lat": round(lat, 5),
                    "lon": round(lon, 5),
                    "nearest_station_id": assigned,
                    "nearest_distance_m": round(nearest_distance, 2),
                    "raw_weight": weight if assigned is not None else 0.0,
                }
            )
            lon += lon_step
        lat += lat_step

    frame = pd.DataFrame(rows)
    assigned = frame[frame["nearest_station_id"].notna()].copy()
    total_weight = assigned["raw_weight"].sum()
    if total_weight <= 0:
        raise RuntimeError(f"No population weights assigned for {city.slug}")
    assigned["population"] = assigned["raw_weight"] / total_weight * city.metro_population
    station_population_series = assigned.groupby("nearest_station_id")["population"].sum()
    for station_id, population in station_population_series.items():
        station_population[str(station_id)] = float(population)

    station_rows = [
        {
            "station_id": station_id,
            "assigned_population": station_population[station_id],
        }
        for station_id in station_population
    ]
    diagnostics = pd.DataFrame(
        [
            {
                "city": city.name,
                "metro_population_target": city.metro_population,
                "assigned_population_total": float(assigned["population"].sum()),
                "assigned_cells": int(len(assigned)),
                "all_cells": int(len(frame)),
                "station_count": int(len(stations)),
                "method_tag": "station_kernel_grid_fallback",
            }
        ]
    )
    return pd.DataFrame(station_rows), diagnostics


def run_city(city: CityConfig, raw_root: Path, table_root: Path, diagnostics_root: Path, geojson_root: Path, refresh: bool = False) -> dict[str, object]:
    raw_path = raw_root / city.slug / "overpass_transit.json"
    fetch_overpass(city, raw_path=raw_path, refresh=refresh)
    overpass_payload = read_json(raw_path)
    if not isinstance(overpass_payload, dict):
        raise RuntimeError(f"Unexpected Overpass payload for {city.slug}")

    stations, segments, _ = _extract_network(overpass_payload, city)
    if len(stations) < 10 or len(segments) < 10:
        raise RuntimeError(f"Transit extraction for {city.slug} produced too little data")

    segments = _add_walking_segments(city, stations, segments)
    anchors = _select_anchors(city, stations)
    anchor_rank_rows: list[dict[str, object]] = []
    anchor_results: dict[str, tuple[dict[str, float], dict[str, int]]] = {}
    for anchor in anchors:
        times, transfers = _run_anchor_dijkstra(city, anchor, stations, segments)
        weighted_reach = float(sum(max(0.0, 120.0 - travel_time) for travel_time in times.values()))
        anchor_results[anchor] = (times, transfers)
        anchor_rank_rows.append(
            {
                "city": city.name,
                "anchor_station_id": anchor,
                "anchor_name": stations[anchor].name,
                "reachable_stations_60min": sum(1 for value in times.values() if value <= 60.0),
                "reachable_stations_120min": sum(1 for value in times.values() if value <= 120.0),
                "weighted_reach_score": weighted_reach,
            }
        )

    anchor_rank = pd.DataFrame(anchor_rank_rows).sort_values(
        ["weighted_reach_score", "reachable_stations_120min"], ascending=[False, False]
    )
    best_anchor_id = str(anchor_rank.iloc[0]["anchor_station_id"])
    best_times, best_transfers = anchor_results[best_anchor_id]

    station_population, population_diag = _build_population_assignment(city, stations)
    station_population_lookup = {
        str(row["station_id"]): float(row["assigned_population"]) for row in station_population.to_dict("records")
    }

    station_rows = []
    for station_id, station in stations.items():
        travel_time = best_times.get(station_id)
        station_rows.append(
            {
                "station_id": station_id,
                "station_name": station.name,
                "latitude": station.lat,
                "longitude": station.lon,
                "best_anchor": stations[best_anchor_id].name,
                "travel_time_minutes": travel_time,
                "transfers_count": best_transfers.get(station_id),
                "assigned_population": station_population_lookup.get(station_id, 0.0),
            }
        )
    station_frame = pd.DataFrame(station_rows).sort_values(["travel_time_minutes", "station_name"], na_position="last")
    write_dataframe(table_root / f"station_times_{city.slug}.csv", station_frame)

    curve_rows = []
    reached = station_frame[station_frame["travel_time_minutes"].notna()].copy()
    for minutes in range(0, 125, 5):
        bucket = reached[reached["travel_time_minutes"] <= minutes]
        curve_rows.append(
            {
                "city": city.name,
                "minutes": minutes,
                "reachable_population": float(bucket["assigned_population"].sum()),
                "reachable_stations": int(len(bucket)),
                "notes": "static_overpass_graph_with_station_kernel_population",
            }
        )
    curve_frame = pd.DataFrame(curve_rows)
    write_dataframe(table_root / f"reachable_population_curve_{city.slug}.csv", curve_frame)

    write_dataframe(diagnostics_root / f"anchor_ranking_{city.slug}.csv", anchor_rank)
    write_dataframe(diagnostics_root / f"population_assignment_{city.slug}.csv", population_diag)

    geojson_features = []
    for row in station_frame.to_dict("records"):
        geojson_features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
                "properties": {
                    "station_id": row["station_id"],
                    "station_name": row["station_name"],
                    "travel_time_minutes": row["travel_time_minutes"],
                    "assigned_population": row["assigned_population"],
                },
            }
        )
    write_json(
        geojson_root / f"station_times_{city.slug}.geojson",
        {"type": "FeatureCollection", "features": geojson_features},
    )

    return {
        "city": city.name,
        "city_slug": city.slug,
        "station_count": int(len(station_frame)),
        "edge_count": int(len(segments)),
        "chosen_anchor": stations[best_anchor_id].name,
        "reachable_population_60min": float(curve_frame[curve_frame["minutes"] == 60]["reachable_population"].iloc[0]),
        "reachable_population_120min": float(curve_frame[curve_frame["minutes"] == 120]["reachable_population"].iloc[0]),
        "raw_source": str(raw_path.relative_to(raw_root.parents[1])),
        "source_notes": "OpenStreetMap via Overpass, with static travel-time approximation",
    }
