from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
RAW_DIR = BASE_DIR / "data" / "raw"
OUTPUT_DIR = BASE_DIR / "outputs"
TABLE_DIR = OUTPUT_DIR / "tables"
DIAGNOSTIC_DIR = OUTPUT_DIR / "diagnostics"
GEOJSON_DIR = OUTPUT_DIR / "geojson"
PLOT_DIR = OUTPUT_DIR / "plots"


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


SPACE_CITY_ASSUMPTIONS = {
    "transfer_penalty_reference_min": 5.0,
    "transfer_penalty_notes": (
        "Earth-analog transfer penalty anchored near 5 minutes. This sits below the 11.24-minute "
        "equivalent in-vehicle penalty reported for Seoul smartcard trips and below the 13-18 minute "
        "planning range proposed in later transfer-penalty literature, because the space-city stations "
        "here are assumed to be purpose-built and low-friction."
    ),
    "atmosphere": {
        "label": "gravity_wheels_in_atmosphere",
        "population": 1_000_000_000,
        "people_per_node": 1_000,
        "grid_shape": (100, 100, 100),
        "cell_spacing_m": 1_000.0,
        "access_time_min": 2.0,
        "egress_time_min": 2.0,
        "transfer_time_min": 5.0,
        "bucket_minutes": 5,
        "max_bucket_minutes": 240,
        "thermal_channel": {
            "channel_width_m": 1_000.0,
            "channel_height_m": 1_000.0,
            "air_density_kg_m3": 1.2,
            "air_specific_heat_j_kg_k": 1_005.0,
            "bulk_air_speed_m_s": 5.0,
            "max_allowed_delta_t_k": 5.0,
            "notes": (
                "Single square ventilation / transport channel running the full length of one side. "
                "The adjacent habitat line dumps waste heat into that channel's passing air stream."
            ),
        },
        "tiers": [
            {
                "name": "local_float_shuttle",
                "cell_span": 1,
                "capacity_people": 24,
                "vehicle_mass_kg": 4_000.0,
                "max_speed_m_s": 22.2,
                "acceleration_m_s2": 1.0,
                "regen_efficiency": 0.65,
                "notes": "Earth-analog automated shuttle scale, using Siemens Airval acceleration as a comfort anchor.",
            },
            {
                "name": "regional_express",
                "cell_span": 5,
                "capacity_people": 192,
                "vehicle_mass_kg": 22_000.0,
                "max_speed_m_s": 60.0,
                "acceleration_m_s2": 0.9,
                "regen_efficiency": 0.70,
                "notes": "Medium-capacity express line inside breathable atmosphere.",
            },
            {
                "name": "trunk_axis_line",
                "cell_span": 25,
                "capacity_people": 1_536,
                "vehicle_mass_kg": 150_000.0,
                "max_speed_m_s": 140.0,
                "acceleration_m_s2": 0.8,
                "regen_efficiency": 0.75,
                "notes": "High-throughput axis trunk constrained to x/y/z lattice corridors.",
            },
        ],
    },
    "vacuum": {
        "label": "rotating_habitats_in_vacuum",
        "population": 1_000_000_000,
        "people_per_node": 10_000,
        "grid_shape": (47, 47, 46),
        "occupied_nodes": 100_000,
        "cell_spacing_m": 3_000.0,
        "access_time_min": 6.0,
        "egress_time_min": 6.0,
        "transfer_time_min": 7.0,
        "bucket_minutes": 5,
        "max_bucket_minutes": 240,
        "pod": {
            "passenger_mass_kg": 90.0,
            "suit_and_restraint_mass_kg": 130.0,
            "pressure_shell_mass_kg": 140.0,
            "localized_shielding_mass_kg": 180.0,
            "battery_avionics_mass_kg": 60.0,
            "docking_hardware_mass_kg": 40.0,
            "notes": (
                "Single-person pod sized as a minimal shielded taxi. The 130 kg suit-and-restraint term "
                "is anchored to NASA's roughly 280-pound spacesuit scale and rounded upward."
            ),
        },
        "tiers": [
            {
                "name": "local_pod_bus",
                "cell_span": 1,
                "capacity_pods": 8,
                "vehicle_mass_kg": 4_000.0,
                "max_speed_m_s": 40.0,
                "acceleration_m_s2": 0.8,
                "regen_efficiency": 0.80,
                "notes": "Short-hop electromagnetic carrier for pod collection and distribution.",
            },
            {
                "name": "regional_pod_bus",
                "cell_span": 4,
                "capacity_pods": 64,
                "vehicle_mass_kg": 20_000.0,
                "max_speed_m_s": 180.0,
                "acceleration_m_s2": 0.9,
                "regen_efficiency": 0.85,
                "notes": "Regional bus between medium hubs on the cubic lattice.",
            },
            {
                "name": "trunk_pod_bus",
                "cell_span": 16,
                "capacity_pods": 512,
                "vehicle_mass_kg": 120_000.0,
                "max_speed_m_s": 500.0,
                "acceleration_m_s2": 1.0,
                "regen_efficiency": 0.90,
                "notes": "Mainline bus on long axis corridors using electromagnetic launch and recovery.",
            },
        ],
    },
    "source_notes": [
        "NASA learning resource mentions a 280-pound spacesuit scale.",
        "Siemens Airval brochure lists 80 km/h maximum speed and 1.3 m/s2 service acceleration.",
        "Seoul transfer-penalty paper reports 11.24 equivalent in-vehicle minutes for CBD trips.",
    ],
}
