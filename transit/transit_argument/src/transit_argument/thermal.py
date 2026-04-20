from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class SphereThermalCase:
    population: int
    watts_per_person: float
    total_heat_w: float
    surface_temperature_k: float
    required_radius_m: float
    required_diameter_m: float
    surface_area_m2: float


def compute_sphere_thermal_bounds(
    population: int,
    watts_per_person: float,
    surface_temperatures_k: list[float],
    sigma: float,
    background_temperature_k: float = 0.0,
) -> pd.DataFrame:
    total_heat = population * watts_per_person
    rows: list[dict[str, float | int]] = []
    for temperature in surface_temperatures_k:
        net_flux = sigma * max(0.0, temperature**4 - background_temperature_k**4)
        if net_flux <= 0:
            raise ValueError("Net flux must be positive")
        area = total_heat / net_flux
        radius = math.sqrt(area / (4.0 * math.pi))
        rows.append(
            {
                "population": population,
                "watts_per_person": watts_per_person,
                "total_heat_W": total_heat,
                "surface_temperature_K": temperature,
                "required_radius_m": radius,
                "required_diameter_m": radius * 2.0,
                "surface_area_m2": area,
            }
        )
    return pd.DataFrame(rows)


def _sample_unit_vectors(count: int, rng: np.random.Generator) -> np.ndarray:
    vec = rng.normal(size=(count, 3))
    norms = np.linalg.norm(vec, axis=1, keepdims=True)
    return vec / norms


def estimate_open_sky_fraction(
    habitat_radius_m: float,
    lattice_spacing_m: float,
    surface_samples: int,
    direction_samples: int,
    neighbor_shell: int,
    seed: int = 7,
) -> float:
    rng = np.random.default_rng(seed)
    normals = _sample_unit_vectors(surface_samples, rng)
    points = normals * habitat_radius_m

    offsets = []
    for x in range(-neighbor_shell, neighbor_shell + 1):
        for y in range(-neighbor_shell, neighbor_shell + 1):
            for z in range(-neighbor_shell, neighbor_shell + 1):
                if x == 0 and y == 0 and z == 0:
                    continue
                offsets.append(np.array([x, y, z], dtype=float) * lattice_spacing_m)
    centers = np.array(offsets)

    clear_count = 0
    total_count = 0
    for point, normal in zip(points, normals):
        direction_vectors = _sample_unit_vectors(direction_samples * 2, rng)
        outward = direction_vectors[(direction_vectors @ normal) > 0][:direction_samples]
        if len(outward) < direction_samples:
            needed = direction_samples - len(outward)
            extra = np.tile(normal, (needed, 1))
            outward = np.vstack([outward, extra])
        for direction in outward:
            total_count += 1
            shifted = point - centers
            b = 2.0 * (shifted @ direction)
            c = np.sum(shifted * shifted, axis=1) - habitat_radius_m**2
            discriminant = b * b - 4.0 * c
            hit = False
            positive = discriminant > 0
            if np.any(positive):
                sqrt_disc = np.sqrt(discriminant[positive])
                roots = (-b[positive] - sqrt_disc) / 2.0
                if np.any(roots > 1e-6):
                    hit = True
            if not hit:
                clear_count += 1
    return clear_count / total_count


def compute_lattice_summary(
    population: int,
    people_per_habitat: int,
    watts_per_person: float,
    habitat_radius_m: float,
    spacing_values_m: list[float],
    surface_samples: int,
    direction_samples: int,
    neighbor_shell: int,
    sky_fraction_threshold: float,
    radiator_temperature_k: float,
    sigma: float,
    background_temperature_k: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    habitat_count = int(math.ceil(population / people_per_habitat))
    total_heat = population * watts_per_person
    radiator_flux = sigma * max(0.0, radiator_temperature_k**4 - background_temperature_k**4)
    single_habitat_area = 4.0 * math.pi * habitat_radius_m**2

    sky_rows: list[dict[str, float | int | bool]] = []
    summary_rows: list[dict[str, float | int | bool | str]] = []
    for spacing in spacing_values_m:
        sky_fraction = estimate_open_sky_fraction(
            habitat_radius_m=habitat_radius_m,
            lattice_spacing_m=spacing,
            surface_samples=surface_samples,
            direction_samples=direction_samples,
            neighbor_shell=neighbor_shell,
            seed=int(spacing),
        )
        threshold_met = sky_fraction >= sky_fraction_threshold
        aggregate_radiating_area = habitat_count * single_habitat_area * sky_fraction
        aggregate_capacity = aggregate_radiating_area * radiator_flux
        thermal_margin = aggregate_capacity / total_heat
        sky_rows.append(
            {
                "habitat_radius_m": habitat_radius_m,
                "lattice_spacing_m": spacing,
                "samples_surface": surface_samples,
                "samples_direction": direction_samples,
                "estimated_open_sky_fraction": sky_fraction,
                "threshold_met": threshold_met,
            }
        )
        summary_rows.append(
            {
                "population": population,
                "people_per_habitat": people_per_habitat,
                "habitat_count": habitat_count,
                "watts_per_person": watts_per_person,
                "total_heat_W": total_heat,
                "habitat_radius_m": habitat_radius_m,
                "lattice_spacing_m": spacing,
                "open_sky_fraction": sky_fraction,
                "threshold_met": threshold_met,
                "aggregate_radiator_area_m2": aggregate_radiating_area,
                "aggregate_radiative_capacity_W": aggregate_capacity,
                "thermal_margin_vs_load": thermal_margin,
                "notes": "Monte Carlo hemisphere escape fraction times total sphere area",
            }
        )
    return pd.DataFrame(sky_rows), pd.DataFrame(summary_rows)
