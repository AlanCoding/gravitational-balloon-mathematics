#!/usr/bin/env python3
"""Build the derived body catalog from the definition layer."""

from __future__ import annotations

import csv
import math
from pathlib import Path


G = 6.67430e-11
G_KM3_S2 = 6.67430e-20
MU_SUN = 1.32712440018e11
AU_KM = 149597870.7
P_MAX = 40e6
EXCAVATION_RHO = 3000.0
TEMP_LIMIT_DEPTH_KM = 2.0


def read_definitions(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def slugify(name: str) -> str:
    chars = []
    last_underscore = False
    for ch in name.lower():
        if ch.isalnum():
            chars.append(ch)
            last_underscore = False
        else:
            if not last_underscore:
                chars.append("_")
                last_underscore = True
    return "".join(chars).strip("_")


def read_orbit_refs(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as f:
        return {row["body_id"]: row for row in csv.DictReader(f)}


def read_asteroid_orbit_refs(path: Path) -> dict[str, dict[str, str]]:
    with path.open(newline="") as f:
        refs = {}
        for row in csv.DictReader(f):
            refs[row["body_id"]] = row
        return refs


def orbit_delta_v(row: dict[str, str], by_id: dict[str, dict[str, str]]) -> float | None:
    kind = row.get("orbit_kind", "")
    if not kind:
        return None
    if row.get("body_id") == "earth":
        return 0.0

    a_km = float(row["orbit_a_km"])
    e = float(row["orbit_e"])
    inc = math.radians(float(row["orbit_i_deg"]))
    q = a_km * (1.0 - e)
    Q = a_km * (1.0 + e)

    if kind == "heliocentric":
        r1 = AU_KM
        r2 = q if abs(q - r1) <= abs(Q - r1) else Q
        a_trans = 0.5 * (r1 + r2)
        v1 = math.sqrt(MU_SUN / r1)
        v2 = math.sqrt(MU_SUN / r2)
        v_tp = math.sqrt(MU_SUN * (2.0 / r1 - 1.0 / a_trans))
        v_ta = math.sqrt(MU_SUN * (2.0 / r2 - 1.0 / a_trans))
        dv_plane = 2.0 * min(v_tp, v_ta) * math.sin(inc / 2.0)
        return abs(v_tp - v1) + abs(v2 - v_ta) + dv_plane

    if kind == "parent-centric":
        parent_id = slugify(row["parent"])
        parent = by_id.get(parent_id)
        if not parent:
            return None
        parent_mass = float(parent["mass_kg"])
        parent_radius_km = float(parent["radius_km"])
        mu_parent = G_KM3_S2 * parent_mass
        r1 = parent_radius_km
        r2 = a_km
        a_trans = 0.5 * (r1 + r2)
        v1 = math.sqrt(mu_parent / r1)
        v2 = math.sqrt(mu_parent / r2)
        v_tp = math.sqrt(mu_parent * (2.0 / r1 - 1.0 / a_trans))
        v_ta = math.sqrt(mu_parent * (2.0 / r2 - 1.0 / a_trans))
        dv_plane = 2.0 * min(v_tp, v_ta) * math.sin(inc / 2.0)
        return abs(v_tp - v1) + abs(v2 - v_ta) + dv_plane

    return None


def escape_velocity_km_s(mass_kg: float, radius_km: float) -> float:
    radius_m = radius_km * 1000.0
    return math.sqrt(2.0 * G * mass_kg / radius_m) / 1000.0


def build_rows(defs: list[dict[str, str]]) -> list[dict[str, str]]:
    orbit_refs = read_orbit_refs(Path("data/origin/orbital_elements.csv"))
    asteroid_refs = read_asteroid_orbit_refs(Path("data/origin/asteroids_dastcom5_reference.csv"))
    rows = []
    for d in defs:
        mass = float(d["mass_kg"])
        radius_km = float(d["radius_km"])
        radius_m = radius_km * 1000.0
        g = G * mass / (radius_m * radius_m)
        bulk_density = mass / ((4.0 / 3.0) * math.pi * radius_m**3)
        pressure_depth_km = P_MAX / (EXCAVATION_RHO * g) / 1000.0
        pressure_bound_km = min(pressure_depth_km, radius_km)
        temperature_bound_km = min(TEMP_LIMIT_DEPTH_KM, radius_km)
        use_depth_km = min(pressure_bound_km, temperature_bound_km)
        pressure_regime = "radius-limited" if pressure_bound_km >= radius_km - 1e-9 else "pressure-limited"
        temperature_regime = "radius-limited" if temperature_bound_km >= radius_km - 1e-9 else "temperature-limited"
        use_regime = "radius-limited" if use_depth_km >= radius_km - 1e-9 else (
            "temperature-limited" if use_depth_km == temperature_bound_km else "pressure-limited"
        )
        reachable_mass = 4.0 * math.pi * EXCAVATION_RHO * (
            radius_m**2 * (use_depth_km * 1000.0)
            - radius_m * (use_depth_km * 1000.0) ** 2
            + (use_depth_km * 1000.0) ** 3 / 3.0
        )
        orbit_row = orbit_refs.get(d["body_id"])
        asteroid_orbit_row = asteroid_refs.get(d["body_id"])
        if asteroid_orbit_row:
            orbit_row = {**(orbit_row or {}), **asteroid_orbit_row}
        delta_v = orbit_delta_v({**orbit_row, "parent": d["parent"], "body_id": d["body_id"]}, {r["body_id"]: r for r in defs}) if orbit_row else None
        rows.append(
            {
                **d,
                "mass_is_computed": "0",
                "radius_is_computed": "0",
                "bulk_density_kg_m3": f"{bulk_density:.6g}",
                "bulk_density_is_computed": "1",
                "surface_gravity_m_s2": f"{g:.6g}",
                "surface_gravity_is_computed": "1",
                "excavation_rho_kg_m3": f"{EXCAVATION_RHO:.6g}",
                "excavation_rho_is_computed": "1",
                "pressure_cap_pa": f"{P_MAX:.6g}",
                "pressure_depth_km": f"{pressure_depth_km:.6g}",
                "pressure_depth_is_computed": "1",
                "temperature_cap_depth_km": f"{TEMP_LIMIT_DEPTH_KM:.6g}",
                "temperature_depth_km": f"{temperature_bound_km:.6g}",
                "temperature_depth_is_computed": "1",
                "usable_depth_km": f"{use_depth_km:.6g}",
                "usable_depth_is_computed": "1",
                "pressure_regime": pressure_regime,
                "temperature_regime": temperature_regime,
                "usable_regime": use_regime,
                "reachable_mass_kg": f"{reachable_mass:.6e}",
                "reachable_mass_is_computed": "1",
                "orbit_kind": orbit_row.get("orbit_kind", "") if orbit_row else "",
                "orbit_center": orbit_row.get("orbit_center", "") if orbit_row else "",
                "orbit_a_km": orbit_row.get("orbit_a_km", "") if orbit_row else "",
                "orbit_e": orbit_row.get("orbit_e", "") if orbit_row else "",
                "orbit_i_deg": orbit_row.get("orbit_i_deg", "") if orbit_row else "",
                "orbit_omega_deg": orbit_row.get("orbit_omega_deg", "") if orbit_row else "",
                "orbit_Omega_deg": orbit_row.get("orbit_Omega_deg", "") if orbit_row else "",
                "orbit_source_id": orbit_row.get("orbit_source_id", "") if orbit_row else "",
                "orbit_delta_v_km_s": f"{delta_v:.6g}" if delta_v is not None else "",
                "orbit_delta_v_is_computed": "1" if delta_v is not None else "0",
                "leo_delta_v_km_s": "",
                "leo_delta_v_is_computed": "0",
            }
        )
    rows.sort(key=lambda r: float(r["mass_kg"]), reverse=True)

    by_id = {r["body_id"]: r for r in rows}
    for r in rows:
        if r["body_id"] == "earth":
            r["leo_delta_v_km_s"] = "0"
            r["leo_delta_v_is_computed"] = "1"
            continue

        orbit_dv = float(r["orbit_delta_v_km_s"]) if r["orbit_delta_v_km_s"] else 0.0
        arrival_bonus = 0.5 * escape_velocity_km_s(float(r["mass_kg"]), float(r["radius_km"]))

        if r["kind"] == "moon":
            parent = by_id.get(slugify(r["parent"]))
            parent_orbit_dv = float(parent["orbit_delta_v_km_s"]) if parent and parent["orbit_delta_v_km_s"] else 0.0
            if r["parent"] == "Earth":
                leo_dv = orbit_dv + arrival_bonus
            else:
                leo_dv = parent_orbit_dv + orbit_dv + arrival_bonus
        else:
            leo_dv = 3.2 + orbit_dv + arrival_bonus

        r["leo_delta_v_km_s"] = f"{leo_dv:.6g}"
        r["leo_delta_v_is_computed"] = "1"
    return rows


def write_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_preview(rows: list[dict[str, str]], path: Path, limit: int = 18) -> None:
    top = rows[:limit]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Body Catalog Preview\n\n")
        f.write("This preview shows the source-truth and computed layers together.\n\n")
        f.write(
            "| Body | Kind | Mass kg | Radius km | Bulk density kg/m^3 | g m/s^2 | Mass src | Radius src | Density computed |\n"
        )
        f.write("| --- | --- | ---: | ---: | ---: | ---: | --- | --- | --- |\n")
        for r in top:
            f.write(
                f"| {r['name']} | {r['kind']} | {float(r['mass_kg']):.6e} | {float(r['radius_km']):.4g} | {float(r['bulk_density_kg_m3']):.4g} | {float(r['surface_gravity_m_s2']):.4g} | {r['mass_source_id']} | {r['radius_source_id']} | {r['bulk_density_is_computed']} |\n"
            )


def main() -> None:
    defs = read_definitions(Path("data/definition/bodies_reference.csv"))
    rows = build_rows(defs)
    write_csv(rows, Path("data/derived/bodies_catalog.csv"))
    write_preview(rows, Path("data/derived/body_catalog_preview.md"))
    print(f"wrote={len(rows)}")


if __name__ == "__main__":
    main()
