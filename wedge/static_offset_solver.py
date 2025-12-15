"""
Solve for static x-offsets of all shells such that every gap carries the same
radial load, given a prescribed hull (shell 0) displacement.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import Tuple

import numpy as np

from positional_250 import (
    N_SHELLS,
    C,
    MU,
    L,
    R,
    U_rel,
    gap_force_magnitudes,
)


MAX_EPS = 0.999  # avoid exactly touching c


def _gap_force_abs(i: int, e: float) -> float:
    if e <= 0.0:
        return 0.0
    Fr, _ = gap_force_magnitudes(e, C[i], MU, U_rel[i], L, R[i])
    return abs(Fr)


def _invert_gap_force(i: int, target_force: float, tol: float = 1e-8) -> float:
    """
    Find the offset e in gap i such that |Fr(e)| = target_force.
    Uses bisection on e ∈ [0, MAX_EPS * c_i].
    """
    if target_force <= 0.0:
        return 0.0

    c_i = C[i]
    lo, hi = 0.0, MAX_EPS * c_i
    f_hi = _gap_force_abs(i, hi)
    if target_force > f_hi:
        raise ValueError(
            f"Target force {target_force:.3e} exceeds max attainable "
            f"{f_hi:.3e} in gap {i}."
        )

    for _ in range(80):
        mid = 0.5 * (lo + hi)
        f_mid = _gap_force_abs(i, mid)
        if abs(f_mid - target_force) < tol:
            return mid
        if f_mid < target_force:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def _propagate_offsets(
    hull_offset: float,
    outer_offset: float,
    target_force: float,
) -> np.ndarray:
    offsets = np.zeros(N_SHELLS, dtype=float)
    offsets[0] = hull_offset
    direction = np.sign(hull_offset - outer_offset)
    if direction == 0.0:
        direction = 1.0

    for i in range(N_SHELLS - 1):
        e = _invert_gap_force(i, target_force)
        offsets[i + 1] = offsets[i] - direction * e

    return offsets


def _max_feasible_force() -> float:
    maxima = []
    for i in range(N_SHELLS - 1):
        maxima.append(_gap_force_abs(i, MAX_EPS * C[i]))
    return min(maxima)


@dataclass
class StaticOffsetResult:
    offsets: np.ndarray  # shape (N_SHELLS,), x offsets
    target_force: float  # magnitude of radial load per gap
    gap_forces: np.ndarray  # |Fr| per gap for the solved offsets


def solve_static_offsets(
    hull_offset: float,
    outer_offset: float = 0.0,
    tol: float = 1e-6,
) -> StaticOffsetResult:
    """
    Solve for x-offsets of all shells so that:
      * shell 0 is fixed at `hull_offset`,
      * shell N-1 is at `outer_offset`,
      * every gap has identical radial load magnitude (|Fr| = constant).
    """
    if abs(hull_offset - outer_offset) < tol:
        offsets = np.full(N_SHELLS, hull_offset, dtype=float)
        return StaticOffsetResult(
            offsets=offsets,
            target_force=0.0,
            gap_forces=np.zeros(N_SHELLS - 1, dtype=float),
        )

    force_lo = 0.0
    force_hi = _max_feasible_force()
    offsets_lo = _propagate_offsets(hull_offset, outer_offset, force_lo)
    err_lo = offsets_lo[-1] - outer_offset
    if err_lo < 0.0:
        raise RuntimeError("Lower force bound already overshoots outer offset.")

    # Ensure we have a high force bound that pushes beyond the target.
    offsets_hi = _propagate_offsets(hull_offset, outer_offset, force_hi)
    err_hi = offsets_hi[-1] - outer_offset
    if err_hi > 0.0:
        raise RuntimeError(
            "Requested hull offset cannot be satisfied within clearance limits."
        )

    for _ in range(80):
        force_mid = 0.5 * (force_lo + force_hi)
        offsets_mid = _propagate_offsets(hull_offset, outer_offset, force_mid)
        err_mid = offsets_mid[-1] - outer_offset
        if abs(err_mid) < tol:
            offsets = offsets_mid
            target_force = force_mid
            break
        if err_mid > 0.0:
            force_lo = force_mid
        else:
            force_hi = force_mid
        offsets = offsets_mid
        target_force = force_mid

    gap_forces = np.zeros(N_SHELLS - 1, dtype=float)
    for i in range(N_SHELLS - 1):
        e = abs(offsets[i] - offsets[i + 1])
        gap_forces[i] = _gap_force_abs(i, e)

    return StaticOffsetResult(offsets=offsets, target_force=target_force, gap_forces=gap_forces)


def _format_offsets(offsets: np.ndarray) -> str:
    lines = [" idx |    x-offset [m]"]
    for idx, x in enumerate(offsets):
        lines.append(f"{idx:4d} | {x:14.6f}")
    return "\n".join(lines)


def _format_forces(gap_forces: np.ndarray) -> str:
    lines = ["gap |   |Fr| [N]"]
    for idx, force in enumerate(gap_forces):
        lines.append(f"{idx:3d} | {force:10.4e}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Solve static offsets for a prescribed hull displacement."
    )
    parser.add_argument(
        "hull_offset",
        type=float,
        help="Desired x-offset of the central tube (m).",
    )
    parser.add_argument(
        "--outer-offset",
        type=float,
        default=0.0,
        help="Target x-offset for the outer envelope (default 0).",
    )
    args = parser.parse_args()

    result = solve_static_offsets(args.hull_offset, args.outer_offset)
    print(_format_offsets(result.offsets))
    print()
    print(_format_forces(result.gap_forces))
    print(f"\nEquilibrium radial load magnitude: {result.target_force:.6e} N")


if __name__ == "__main__":
    main()
