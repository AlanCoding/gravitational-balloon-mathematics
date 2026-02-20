from __future__ import annotations

from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt


def _eps_tag(epsilon: float) -> str:
    return str(epsilon).replace(".", "p")


def _legend_bottom_center(ax: plt.Axes) -> None:
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 0.02), framealpha=0.9)


def plot_thermal(
    *,
    out_dir: Path,
    material: str,
    epsilon: float,
    R_km: np.ndarray,
    qppp_max: np.ndarray,
    q_expected: float,
    xscale: str,
) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(R_km, qppp_max, label=f"Allowable q''' max (eps={epsilon:g})")
    ax.axhline(q_expected, linestyle="--", label=f"Expected q''' = {q_expected:g} W/m^3")
    ok = qppp_max >= q_expected
    ax.fill_between(R_km, q_expected, qppp_max, where=ok, alpha=0.2, label="Thermally feasible")
    ax.set_xscale(xscale)
    ax.set_yscale("log")
    ax.set_xlabel("R (km)")
    ax.set_ylabel("Volumetric heat generation q''' (W/m^3)")
    ax.set_title(f"Thermal Limit vs Radius ({material}, eps={epsilon:g})")
    _legend_bottom_center(ax)
    ax.grid(True, which="both", alpha=0.3)
    out_path = out_dir / f"thermal_{material}_eps{_eps_tag(epsilon)}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def plot_shielding(
    *,
    out_dir: Path,
    material: str,
    R_km: np.ndarray,
    mu_wall: np.ndarray,
    mu_req: float,
    xscale: str,
) -> Path:
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(R_km, mu_wall, label="Wall areal mass mu_wall")
    ax.axhline(mu_req, linestyle="--", label=f"Required mu_req = {mu_req:g} kg/m^2")
    ok = mu_wall >= mu_req
    ax.fill_between(R_km, mu_req, mu_wall, where=ok, alpha=0.2, label="Shielding feasible")
    ax.set_xscale(xscale)
    ax.set_yscale("log")
    ax.set_xlabel("R (km)")
    ax.set_ylabel("Areal mass mu (kg/m^2)")
    ax.set_title(f"Shielding Limit vs Radius ({material})")
    _legend_bottom_center(ax)
    ax.grid(True, which="both", alpha=0.3)
    out_path = out_dir / f"shielding_{material}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path


def plot_combined(
    *,
    out_dir: Path,
    material: str,
    epsilon: float,
    R_km: np.ndarray,
    qppp_max: np.ndarray,
    q_expected: float,
    mu_wall: np.ndarray,
    mu_req: float,
    xscale: str,
) -> Path:
    fig, ax1 = plt.subplots(figsize=(10, 5.5))
    ax2 = ax1.twinx()

    l1 = ax1.plot(R_km, qppp_max, label="Allowable q''' max")
    l2 = ax1.axhline(q_expected, linestyle="--", label="Expected q'''")
    l3 = ax2.plot(R_km, mu_wall, color="red", label="Wall areal mass mu_wall")
    l4 = ax2.axhline(mu_req, linestyle="--", color="red", label="Required mu_req")

    ok_thermal = qppp_max >= q_expected
    ok_shielding = mu_wall >= mu_req
    both = ok_thermal & ok_shielding
    thermal_only = ok_thermal & (~ok_shielding)
    shielding_only = ok_shielding & (~ok_thermal)

    ax1.fill_between(R_km, 0, 1, where=both, alpha=0.12, color="green", transform=ax1.get_xaxis_transform(), label="both")
    ax1.fill_between(
        R_km,
        0,
        1,
        where=thermal_only,
        alpha=0.12,
        color="yellow",
        transform=ax1.get_xaxis_transform(),
        label="thermal only",
    )
    ax1.fill_between(
        R_km,
        0,
        1,
        where=shielding_only,
        alpha=0.12,
        color="blue",
        transform=ax1.get_xaxis_transform(),
        label="shielding only",
    )

    ax1.set_xscale(xscale)
    ax1.set_yscale("log")
    ax2.set_yscale("log")
    ax1.set_xlabel("R (km)")
    ax1.set_ylabel("q''' (W/m^3)")
    ax2.set_ylabel("mu (kg/m^2)")
    ax1.set_title(f"Combined Thermal + Shielding Feasibility ({material}, eps={epsilon:g})")
    ax1.grid(True, which="both", alpha=0.3)
    ax1.text(
        0.2,
        0.5,
        "insufficient shielding",
        transform=ax1.transAxes,
        ha="center",
        va="center",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
    )
    ax1.text(
        0.8,
        0.5,
        "heat limited",
        transform=ax1.transAxes,
        ha="center",
        va="center",
        bbox={"boxstyle": "round,pad=0.3", "facecolor": "white", "alpha": 0.8},
    )

    handles = [l1[0], l2, l3[0], l4]
    labels = [h.get_label() for h in handles]
    ax1.legend(handles, labels, loc="lower center", bbox_to_anchor=(0.5, 0.02), framealpha=0.9)

    out_path = out_dir / f"combined_{material}_eps{_eps_tag(epsilon)}.png"
    fig.tight_layout()
    fig.savefig(out_path, dpi=160)
    plt.close(fig)
    return out_path
