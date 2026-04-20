from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
DIAGNOSTIC_DIR = OUTPUT_DIR / "diagnostics"
GEOJSON_DIR = OUTPUT_DIR / "geojson"


@dataclass(frozen=True)
class CityConfig:
    slug: str
    name: str
    bbox: tuple[float, float, float, float]
    center: tuple[float, float]
    anchor_candidates: tuple[str, ...]
    metro_population: int
    route_modes: tuple[str, ...] = ("subway", "light_rail", "train", "monorail")
    density_kernel_km: float = 4.5
    catchment_radius_km: float = 6.0
    walking_speed_kmh: float = 4.8
    max_walking_link_m: float = 450.0
    entry_penalty_min: float = 4.0
    exit_penalty_min: float = 3.0
    transfer_penalty_min: float = 5.0
    dwell_time_min: float = 0.75
    speed_overrides_kmh: dict[str, float] = field(
        default_factory=lambda: {
            "subway": 34.0,
            "light_rail": 28.0,
            "monorail": 32.0,
            "train": 42.0,
        }
    )
    sources: tuple[str, ...] = (
        "OpenStreetMap transit routes and stations via Overpass API",
        "Config-specified metro population totals",
        "Station-kernel density fallback for population attachment",
    )


CITIES: dict[str, CityConfig] = {
    "new_york": CityConfig(
        slug="new_york",
        name="New York",
        bbox=(40.57, -74.05, 40.91, -73.72),
        center=(40.7527, -73.9772),
        anchor_candidates=("Times Sq", "Grand Central", "34 St", "Herald Sq"),
        metro_population=19_500_000,
        route_modes=("subway", "light_rail"),
    ),
    "london": CityConfig(
        slug="london",
        name="London",
        bbox=(51.30, -0.36, 51.69, 0.12),
        center=(51.5074, -0.1278),
        anchor_candidates=("King's Cross", "Oxford Circus", "Waterloo", "Bank"),
        metro_population=14_800_000,
        route_modes=("subway", "light_rail"),
    ),
    "paris": CityConfig(
        slug="paris",
        name="Paris",
        bbox=(48.81, 2.25, 48.90, 2.41),
        center=(48.8566, 2.3522),
        anchor_candidates=("Châtelet", "Gare du Nord", "Saint-Lazare", "Nation"),
        metro_population=12_300_000,
        route_modes=("subway", "light_rail"),
    ),
    "tokyo": CityConfig(
        slug="tokyo",
        name="Tokyo",
        bbox=(35.64, 139.69, 35.75, 139.82),
        center=(35.6812, 139.7671),
        anchor_candidates=("Shinjuku", "Tokyo", "Otemachi", "Ikebukuro"),
        metro_population=37_400_000,
        route_modes=("subway",),
    ),
    "seoul": CityConfig(
        slug="seoul",
        name="Seoul",
        bbox=(37.49, 126.91, 37.61, 127.06),
        center=(37.5665, 126.9780),
        anchor_candidates=("Seoul Station", "City Hall", "Gangnam", "Wangsimni"),
        metro_population=26_000_000,
        route_modes=("subway", "light_rail"),
    ),
    "hong_kong": CityConfig(
        slug="hong_kong",
        name="Hong Kong",
        bbox=(22.25, 113.95, 22.42, 114.26),
        center=(22.3193, 114.1694),
        anchor_candidates=("Central", "Admiralty", "Kowloon Tong", "Prince Edward"),
        metro_population=7_500_000,
        route_modes=("subway", "light_rail"),
    ),
}


THERMAL_ASSUMPTIONS = {
    "population": 1_000_000_000,
    "watts_per_person": 20_000.0,
    "surface_temperatures_k": [273.15, 283.15, 293.15, 303.15],
    "background_temperature_k": 0.0,
    "stefan_boltzmann_constant": 5.670374419e-8,
}


LATTICE_ASSUMPTIONS = {
    "population": 1_000_000_000,
    "people_per_habitat": 10_000,
    "watts_per_person": 20_000.0,
    "habitat_radius_m": 500.0,
    "spacing_values_m": [
        1_200.0,
        1_500.0,
        1_800.0,
        2_200.0,
        2_600.0,
        3_000.0,
        3_600.0,
        4_500.0,
        5_500.0,
        7_000.0,
        9_000.0,
        12_000.0,
    ],
    "sky_fraction_threshold": 2.0 / 3.0,
    "surface_samples": 180,
    "direction_samples": 220,
    "neighbor_shell": 3,
    "radiator_temperature_k": 293.15,
    "background_temperature_k": 0.0,
    "stefan_boltzmann_constant": 5.670374419e-8,
}
