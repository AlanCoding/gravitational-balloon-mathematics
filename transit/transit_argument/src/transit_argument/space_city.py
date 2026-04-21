from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from transit_argument.config import PLOT_DIR, TABLE_DIR
from transit_argument.io_utils import write_dataframe


@dataclass(frozen=True)
class TierSpec:
    name: str
    cell_span: int
    capacity_units: int
    vehicle_mass_kg: float
    max_speed_m_s: float
    acceleration_m_s2: float
    regen_efficiency: float
    notes: str


@dataclass(frozen=True)
class MobilityCase:
    slug: str
    label: str
    population: int
    people_per_node: float
    grid_shape: tuple[int, int, int]
    cell_spacing_m: float
    access_time_min: float
    egress_time_min: float
    transfer_time_min: float
    tiers: tuple[TierSpec, ...]
    occupied_nodes: int | None = None
    pod_mass_kg: float | None = None
    pod_notes: str | None = None


def trapezoid_motion(distance_m: float, max_speed_m_s: float, acceleration_m_s2: float) -> tuple[float, float]:
    if distance_m <= 0:
        return 0.0, 0.0
    accel_distance = max_speed_m_s * max_speed_m_s / acceleration_m_s2
    if distance_m <= accel_distance:
        peak_speed = math.sqrt(distance_m * acceleration_m_s2)
        motion_time_s = 2.0 * peak_speed / acceleration_m_s2
        return motion_time_s, peak_speed
    cruise_distance = distance_m - accel_distance
    motion_time_s = 2.0 * max_speed_m_s / acceleration_m_s2 + cruise_distance / max_speed_m_s
    return motion_time_s, max_speed_m_s


def _axis_lookup(max_delta: int, case: MobilityCase) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ordered_tiers = sorted(case.tiers, key=lambda tier: tier.cell_span, reverse=True)
    motion_time_min = np.zeros(max_delta + 1)
    segment_counts = np.zeros(max_delta + 1, dtype=int)
    net_energy_kwh = np.zeros(max_delta + 1)

    for delta in range(1, max_delta + 1):
        remainder = delta
        for tier in ordered_tiers:
            if remainder <= 0:
                break
            segment_units = remainder // tier.cell_span
            if segment_units <= 0:
                continue
            segment_distance_m = segment_units * tier.cell_span * case.cell_spacing_m
            segment_time_s, peak_speed = trapezoid_motion(
                distance_m=segment_distance_m,
                max_speed_m_s=tier.max_speed_m_s,
                acceleration_m_s2=tier.acceleration_m_s2,
            )
            motion_time_min[delta] += segment_time_s / 60.0
            segment_counts[delta] += 1
            kinetic_energy_j = 0.5 * tier.vehicle_mass_kg * peak_speed * peak_speed
            net_energy_kwh[delta] += (
                kinetic_energy_j * (1.0 - tier.regen_efficiency) / 3_600_000.0 / tier.capacity_units
            )
            remainder -= segment_units * tier.cell_span
    return motion_time_min, segment_counts, net_energy_kwh


def build_case(case_name: str, raw: dict[str, object]) -> MobilityCase:
    tiers: list[TierSpec] = []
    if case_name == "vacuum":
        pod = raw["pod"]
        pod_mass = float(
            pod["passenger_mass_kg"]
            + pod["suit_and_restraint_mass_kg"]
            + pod["pressure_shell_mass_kg"]
            + pod["localized_shielding_mass_kg"]
            + pod["battery_avionics_mass_kg"]
            + pod["docking_hardware_mass_kg"]
        )
        for tier in raw["tiers"]:
            tiers.append(
                TierSpec(
                    name=str(tier["name"]),
                    cell_span=int(tier["cell_span"]),
                    capacity_units=int(tier["capacity_pods"]),
                    vehicle_mass_kg=float(tier["vehicle_mass_kg"]) + pod_mass * int(tier["capacity_pods"]),
                    max_speed_m_s=float(tier["max_speed_m_s"]),
                    acceleration_m_s2=float(tier["acceleration_m_s2"]),
                    regen_efficiency=float(tier["regen_efficiency"]),
                    notes=str(tier["notes"]),
                )
            )
        return MobilityCase(
            slug=case_name,
            label=str(raw["label"]),
            population=int(raw["population"]),
            people_per_node=float(raw["people_per_node"]),
            grid_shape=tuple(int(value) for value in raw["grid_shape"]),
            cell_spacing_m=float(raw["cell_spacing_m"]),
            access_time_min=float(raw["access_time_min"]),
            egress_time_min=float(raw["egress_time_min"]),
            transfer_time_min=float(raw["transfer_time_min"]),
            tiers=tuple(tiers),
            occupied_nodes=int(raw["occupied_nodes"]),
            pod_mass_kg=pod_mass,
            pod_notes=str(pod["notes"]),
        )

    for tier in raw["tiers"]:
        tiers.append(
            TierSpec(
                name=str(tier["name"]),
                cell_span=int(tier["cell_span"]),
                capacity_units=int(tier["capacity_people"]),
                vehicle_mass_kg=float(tier["vehicle_mass_kg"]),
                max_speed_m_s=float(tier["max_speed_m_s"]),
                acceleration_m_s2=float(tier["acceleration_m_s2"]),
                regen_efficiency=float(tier["regen_efficiency"]),
                notes=str(tier["notes"]),
            )
        )
    return MobilityCase(
        slug=case_name,
        label=str(raw["label"]),
        population=int(raw["population"]),
        people_per_node=float(raw["people_per_node"]),
        grid_shape=tuple(int(value) for value in raw["grid_shape"]),
        cell_spacing_m=float(raw["cell_spacing_m"]),
        access_time_min=float(raw["access_time_min"]),
        egress_time_min=float(raw["egress_time_min"]),
        transfer_time_min=float(raw["transfer_time_min"]),
        tiers=tuple(tiers),
    )


def compute_atmosphere_channel_thermal(raw_case: dict[str, object], watts_per_person: float) -> pd.DataFrame:
    dims = tuple(int(value) for value in raw_case["grid_shape"])
    channel = raw_case["thermal_channel"]
    people_per_node = float(raw_case["people_per_node"])
    spacing_m = float(raw_case["cell_spacing_m"])
    line_node_count = dims[0]
    side_length_m = line_node_count * spacing_m
    line_population = line_node_count * people_per_node
    line_heat_w = line_population * watts_per_person

    channel_width_m = float(channel["channel_width_m"])
    channel_height_m = float(channel["channel_height_m"])
    channel_area_m2 = channel_width_m * channel_height_m
    channel_volume_m3 = channel_area_m2 * side_length_m
    air_density = float(channel["air_density_kg_m3"])
    air_specific_heat = float(channel["air_specific_heat_j_kg_k"])
    air_mass_kg = channel_volume_m3 * air_density
    heat_capacity_j_k = air_mass_kg * air_specific_heat
    heating_rate_k_s = line_heat_w / heat_capacity_j_k

    bulk_air_speed_m_s = float(channel["bulk_air_speed_m_s"])
    residence_time_s = side_length_m / bulk_air_speed_m_s
    channel_airflow_kg_s = channel_area_m2 * bulk_air_speed_m_s * air_density
    single_pass_delta_t_k = line_heat_w / (channel_airflow_kg_s * air_specific_heat)

    max_allowed_delta_t_k = float(channel["max_allowed_delta_t_k"])
    required_air_mass_flow_kg_s = line_heat_w / (air_specific_heat * max_allowed_delta_t_k)
    required_air_speed_m_s = required_air_mass_flow_kg_s / (air_density * channel_area_m2)

    return pd.DataFrame(
        [
            {
                "case": str(raw_case["label"]),
                "line_node_count": line_node_count,
                "side_length_m": side_length_m,
                "line_population": line_population,
                "watts_per_person": watts_per_person,
                "line_heat_W": line_heat_w,
                "channel_width_m": channel_width_m,
                "channel_height_m": channel_height_m,
                "channel_cross_section_area_m2": channel_area_m2,
                "channel_volume_m3": channel_volume_m3,
                "air_density_kg_m3": air_density,
                "air_specific_heat_j_kg_k": air_specific_heat,
                "channel_air_mass_kg": air_mass_kg,
                "channel_heat_capacity_j_k": heat_capacity_j_k,
                "bulk_air_speed_m_s": bulk_air_speed_m_s,
                "air_residence_time_s": residence_time_s,
                "channel_air_mass_flow_kg_s": channel_airflow_kg_s,
                "air_heating_rate_k_per_s": heating_rate_k_s,
                "air_heating_rate_k_per_hour": heating_rate_k_s * 3600.0,
                "single_pass_delta_t_k": single_pass_delta_t_k,
                "max_allowed_delta_t_k": max_allowed_delta_t_k,
                "required_air_mass_flow_kg_s_for_limit": required_air_mass_flow_kg_s,
                "required_air_speed_m_s_for_limit": required_air_speed_m_s,
                "within_limit_at_configured_speed": single_pass_delta_t_k <= max_allowed_delta_t_k,
                "notes": str(channel["notes"]),
            }
        ]
    )


def _occupancy_mask(case: MobilityCase) -> np.ndarray:
    dims = case.grid_shape
    total_cells = dims[0] * dims[1] * dims[2]
    if case.occupied_nodes is None or case.occupied_nodes >= total_cells:
        return np.ones(dims, dtype=bool)

    indices = np.indices(dims)
    center = np.array([(size - 1) / 2.0 for size in dims], dtype=float).reshape(3, 1, 1, 1)
    squared_distance = np.sum((indices - center) ** 2, axis=0)
    flat_order = np.argsort(squared_distance.ravel(), kind="stable")
    mask = np.zeros(total_cells, dtype=bool)
    mask[flat_order[: case.occupied_nodes]] = True
    return mask.reshape(dims)


def compute_case_outputs(case: MobilityCase, bucket_minutes: int, max_bucket_minutes: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    dims = case.grid_shape
    origin = tuple(size // 2 for size in dims)
    occupancy = _occupancy_mask(case)

    axis_motion: list[np.ndarray] = []
    axis_segments: list[np.ndarray] = []
    axis_energy: list[np.ndarray] = []
    for size in dims:
        motion, segments, energy = _axis_lookup(size - 1, case)
        axis_motion.append(motion)
        axis_segments.append(segments)
        axis_energy.append(energy)

    grid = np.indices(dims)
    dx = np.abs(grid[0] - origin[0])
    dy = np.abs(grid[1] - origin[1])
    dz = np.abs(grid[2] - origin[2])

    motion = axis_motion[0][dx] + axis_motion[1][dy] + axis_motion[2][dz]
    segments = axis_segments[0][dx] + axis_segments[1][dy] + axis_segments[2][dz]
    energy = axis_energy[0][dx] + axis_energy[1][dy] + axis_energy[2][dz]

    transfer_penalty = np.where(segments > 0, (segments - 1) * case.transfer_time_min, 0.0)
    total_time = np.where(
        segments > 0,
        case.access_time_min + case.egress_time_min + motion + transfer_penalty,
        0.0,
    )

    flat_time = total_time[occupancy].ravel()
    flat_energy = energy[occupancy].ravel()
    per_destination_population = case.population / flat_time.size
    reachable_rows = []
    for minutes in range(0, max_bucket_minutes + bucket_minutes, bucket_minutes):
        mask = flat_time <= minutes
        reachable_rows.append(
            {
                "case": case.label,
                "minutes": minutes,
                "reachable_population": float(mask.sum() * per_destination_population),
                "reachable_nodes": int(mask.sum()),
                "share_of_population": float(mask.mean()),
                "method_tag": "axis_aligned_tiered_bus_lattice",
            }
        )
    curve = pd.DataFrame(reachable_rows)

    summary = pd.DataFrame(
        [
            {
                "case": case.label,
                "population": case.population,
                "node_count": flat_time.size,
                "people_per_node_effective": per_destination_population,
                "mean_travel_time_min": float(np.average(flat_time)),
                "median_travel_time_min": float(np.quantile(flat_time, 0.5)),
                "p90_travel_time_min": float(np.quantile(flat_time, 0.9)),
                "p99_travel_time_min": float(np.quantile(flat_time, 0.99)),
                "max_travel_time_min": float(np.max(flat_time)),
                "mean_net_kinetic_energy_kwh": float(np.average(flat_energy)),
                "p90_net_kinetic_energy_kwh": float(np.quantile(flat_energy, 0.9)),
                "grid_shape": "x".join(str(value) for value in dims),
                "cell_spacing_m": case.cell_spacing_m,
                "access_time_min": case.access_time_min,
                "egress_time_min": case.egress_time_min,
                "transfer_time_min": case.transfer_time_min,
            }
        ]
    )

    tier_rows = []
    for tier in case.tiers:
        tier_rows.append(
            {
                "case": case.label,
                "tier_name": tier.name,
                "cell_span": tier.cell_span,
                "cell_distance_m": tier.cell_span * case.cell_spacing_m,
                "capacity_units": tier.capacity_units,
                "vehicle_mass_kg": tier.vehicle_mass_kg,
                "max_speed_m_s": tier.max_speed_m_s,
                "max_speed_km_h": tier.max_speed_m_s * 3.6,
                "acceleration_m_s2": tier.acceleration_m_s2,
                "regen_efficiency": tier.regen_efficiency,
                "full_speed_kinetic_energy_kwh_per_vehicle": 0.5
                * tier.vehicle_mass_kg
                * tier.max_speed_m_s
                * tier.max_speed_m_s
                / 3_600_000.0,
                "net_cycle_energy_kwh_per_passenger_at_full_load": 0.5
                * tier.vehicle_mass_kg
                * tier.max_speed_m_s
                * tier.max_speed_m_s
                * (1.0 - tier.regen_efficiency)
                / 3_600_000.0
                / tier.capacity_units,
                "notes": tier.notes,
            }
        )
    if case.pod_mass_kg is not None:
        tier_rows.append(
            {
                "case": case.label,
                "tier_name": "single_person_pod",
                "cell_span": 0,
                "cell_distance_m": 0.0,
                "capacity_units": 1,
                "vehicle_mass_kg": case.pod_mass_kg,
                "max_speed_m_s": np.nan,
                "max_speed_km_h": np.nan,
                "acceleration_m_s2": np.nan,
                "regen_efficiency": np.nan,
                "notes": case.pod_notes,
            }
        )
    return curve, summary, pd.DataFrame(tier_rows)


def write_space_city_plot(curves: list[pd.DataFrame], output_prefix: Path) -> None:
    output_prefix.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(10, 6))
    colors = {
        "gravity_wheels_in_atmosphere": "#005f73",
        "rotating_habitats_in_vacuum": "#ae2012",
    }
    for curve in curves:
        label = str(curve.iloc[0]["case"])
        ax.plot(
            curve["minutes"],
            curve["reachable_population"] / 1_000_000.0,
            linewidth=2.5,
            label=label.replace("_", " "),
            color=colors.get(label, None),
        )
    ax.set_xlabel("Travel time (minutes)")
    ax.set_ylabel("Reachable population (millions)")
    ax.set_title("Reachable Population vs Time for 1-Billion-Person Space Cities")
    ax.grid(alpha=0.25)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(output_prefix.with_suffix(".png"), dpi=180)
    fig.savefig(output_prefix.with_suffix(".svg"))
    plt.close(fig)


def build_space_city_outputs(cases: list[MobilityCase], bucket_minutes: int, max_bucket_minutes: int) -> None:
    curves: list[pd.DataFrame] = []
    summaries: list[pd.DataFrame] = []
    tiers: list[pd.DataFrame] = []
    for case in cases:
        curve, summary, tier_table = compute_case_outputs(case, bucket_minutes=bucket_minutes, max_bucket_minutes=max_bucket_minutes)
        curves.append(curve)
        summaries.append(summary)
        tiers.append(tier_table)
        write_dataframe(TABLE_DIR / f"reachable_population_curve_space_city_{case.slug}.csv", curve)
        write_dataframe(TABLE_DIR / f"space_city_trip_summary_{case.slug}.csv", summary)
        write_dataframe(TABLE_DIR / f"space_city_tiers_{case.slug}.csv", tier_table)

    combined_summary = pd.concat(summaries, ignore_index=True)
    write_dataframe(TABLE_DIR / "space_city_trip_summary.csv", combined_summary)
    combined_curves = pd.concat(curves, ignore_index=True)
    write_dataframe(TABLE_DIR / "space_city_reachable_population_curves.csv", combined_curves)
    combined_tiers = pd.concat(tiers, ignore_index=True)
    write_dataframe(TABLE_DIR / "space_city_tiers.csv", combined_tiers)
    write_space_city_plot(curves, PLOT_DIR / "space_city_reachable_population_vs_time")
