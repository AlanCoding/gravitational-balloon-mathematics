#!/usr/bin/env python3
"""Extract a small asteroid catalog from the local DASTCOM5 binary.

This reads the asteroid database in the checked-in JPL dump, pulls the fields
needed for mass/radius work, and writes a full CSV plus a small markdown
preview table.
"""

from __future__ import annotations

import argparse
import csv
import math
import mmap
import struct
from dataclasses import dataclass
from pathlib import Path


RECL = 835
G_KM3_S2 = 6.67430e-20  # km^3 / (kg s^2)
P_MAX = 40e6
EXCAVATION_RHO = 3000.0

# DASTCOM5 asteroid record offsets are byte offsets from the start of the
# physical record, zero-based.
NO_OFF = 0
OM_OFF = 48
IN_OFF = 56
EC_OFF = 64
A_OFF = 72
MA_OFF = 40
RP_OFF = 560
GM_OFF = 564
RAD_OFF = 568
NAME_OFF = 817
NAME_LEN = 18
AU_KM = 149597870.7


@dataclass(frozen=True)
class AsteroidRow:
    no: int
    name: str
    rp_hr: float
    gm_km3_s2: float
    radius_km: float
    mass_kg: float
    orbit_a_au: float
    orbit_e: float
    orbit_i_deg: float
    orbit_Omega_deg: float
    orbit_ma_deg: float
    orbit_q_au: float
    orbit_Q_au: float


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--input",
        default="dastcom5/dat/dast5_le.dat",
        help="Path to the little-endian DASTCOM5 asteroid binary.",
    )
    p.add_argument(
        "--out-csv",
        default="data/origin/asteroids_dastcom5_reference.csv",
        help="Write the extracted catalog here.",
    )
    p.add_argument(
        "--out-preview",
        default="data/derived/asteroid_mass_preview.md",
        help="Write a small markdown preview table here.",
    )
    p.add_argument(
        "--preview-limit",
        type=int,
        default=20,
        help="Number of rows to include in the preview table.",
    )
    return p.parse_args()


def read_rows(path: Path) -> list[AsteroidRow]:
    rows: list[AsteroidRow] = []
    with path.open("rb") as f:
        mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
        n_records = len(mm) // RECL
        for rec in range(2, n_records + 1):
            off = (rec - 1) * RECL
            no = struct.unpack_from("<i", mm, off + NO_OFF)[0]
            name = mm[off + NAME_OFF : off + NAME_OFF + NAME_LEN].decode(
                "ascii", errors="ignore"
            ).strip()
            if not name:
                continue
            rp = struct.unpack_from("<f", mm, off + RP_OFF)[0]
            gm = struct.unpack_from("<f", mm, off + GM_OFF)[0]
            rad = struct.unpack_from("<f", mm, off + RAD_OFF)[0]
            a = struct.unpack_from("<d", mm, off + A_OFF)[0]
            e = struct.unpack_from("<d", mm, off + EC_OFF)[0]
            inc = struct.unpack_from("<d", mm, off + IN_OFF)[0]
            om = struct.unpack_from("<d", mm, off + OM_OFF)[0]
            ma = struct.unpack_from("<d", mm, off + MA_OFF)[0]
            if not (math.isfinite(gm) and math.isfinite(rad) and gm > 0 and rad > 0):
                continue
            mass_kg = gm / G_KM3_S2
            q = a * (1.0 - e)
            Q = a * (1.0 + e)
            rows.append(
                AsteroidRow(
                    no=no,
                    name=name,
                    rp_hr=rp,
                    gm_km3_s2=gm,
                    radius_km=rad,
                    mass_kg=mass_kg,
                    orbit_a_au=a,
                    orbit_e=e,
                    orbit_i_deg=inc,
                    orbit_Omega_deg=om,
                    orbit_ma_deg=ma,
                    orbit_q_au=q,
                    orbit_Q_au=Q,
                )
            )
    return rows


def write_csv(rows: list[AsteroidRow], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["body_id", "no", "name", "rp_hr", "gm_km3_s2", "radius_km", "mass_kg", "orbit_a_km", "orbit_e", "orbit_i_deg", "orbit_Omega_deg", "orbit_ma_deg", "orbit_q_km", "orbit_Q_km"])
        for row in rows:
            body_id = row.name.lower().replace(" ", "_")
            w.writerow([body_id, row.no, row.name, f"{row.rp_hr:.6g}", f"{row.gm_km3_s2:.6g}", f"{row.radius_km:.6g}", f"{row.mass_kg:.6e}", f"{row.orbit_a_au * AU_KM:.8g}", f"{row.orbit_e:.8g}", f"{row.orbit_i_deg:.8g}", f"{row.orbit_Omega_deg:.8g}", f"{row.orbit_ma_deg:.8g}", f"{row.orbit_q_au * AU_KM:.8g}", f"{row.orbit_Q_au * AU_KM:.8g}"])


def write_preview(rows: list[AsteroidRow], path: Path, limit: int) -> None:
    top = sorted(rows, key=lambda r: r.mass_kg, reverse=True)[:limit]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Asteroid Mass Preview\n\n")
        f.write("Top bodies with both `GM` and `RAD` present in the local DASTCOM5 dump.\n\n")
        f.write("| NO | Name | Rotation hr | GM km^3/s^2 | Radius km | Mass kg |\n")
        f.write("| ---: | --- | ---: | ---: | ---: | ---: |\n")
        for row in top:
            f.write(
                f"| {row.no} | {row.name} | {row.rp_hr:.4g} | {row.gm_km3_s2:.6g} | {row.radius_km:.4g} | {row.mass_kg:.6e} |\n"
            )


def write_mining_preview(rows: list[AsteroidRow], path: Path, limit: int) -> None:
    top = sorted(rows, key=lambda r: r.mass_kg, reverse=True)[:limit]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        f.write("# Asteroid Mining Preview\n\n")
        f.write(f"Pressure cap: `{P_MAX/1e6:.0f} MPa`\n\n")
        f.write("This uses a simplified excavation density of `3000 kg/m^3`.\n\n")
        f.write("| NO | Name | Mass kg | Radius km | g m/s^2 | Pressure depth km | Accessible km | Regime |\n")
        f.write("| ---: | --- | ---: | ---: | ---: | ---: | ---: | --- |\n")
        for row in top:
            g = row.gm_km3_s2 * 1e3 / (row.radius_km ** 2)
            depth_km = P_MAX / (EXCAVATION_RHO * g) / 1000.0
            accessible_km = min(depth_km, row.radius_km)
            regime = "radius-limited" if accessible_km >= row.radius_km - 1e-9 else "pressure-limited"
            f.write(
                f"| {row.no} | {row.name} | {row.mass_kg:.6e} | {row.radius_km:.4g} | {g:.6f} | {depth_km:.3f} | {accessible_km:.3f} | {regime} |\n"
            )


def main() -> None:
    args = parse_args()
    rows = read_rows(Path(args.input))
    write_csv(rows, Path(args.out_csv))
    write_preview(rows, Path(args.out_preview), args.preview_limit)
    write_mining_preview(rows, Path("data/derived/asteroid_mining_preview.md"), args.preview_limit)
    print(f"extracted={len(rows)}")


if __name__ == "__main__":
    main()
