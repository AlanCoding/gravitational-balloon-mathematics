from __future__ import annotations

from typing import Callable

from hab_sphere.physics import temperatures


def _target_temp(
    *,
    target: str,
    R_m: float,
    qppp: float,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
) -> float:
    T_in_surf, T_air, _ = temperatures(
        R_m=R_m,
        qppp=qppp,
        p=p,
        sigma_allow=sigma_allow,
        k=k,
        epsilon=epsilon,
        T_space=T_space,
        h_i=h_i,
    )
    if target == "inner_surface":
        return T_in_surf
    if target == "air":
        return T_air
    raise ValueError(f"Unknown temp target: {target}")


def solve_qppp_max(
    *,
    R_m: float,
    T_in_max: float,
    target: str,
    p: float,
    sigma_allow: float,
    k: float,
    epsilon: float,
    T_space: float,
    h_i: float,
    q_high_init: float = 1e-3,
    q_hard_cap: float = 1e6,
    max_expand_iters: int = 80,
    max_bisect_iters: int = 120,
    tol_abs: float = 1e-9,
) -> float:
    def f(qppp: float) -> float:
        return (
            _target_temp(
                target=target,
                R_m=R_m,
                qppp=qppp,
                p=p,
                sigma_allow=sigma_allow,
                k=k,
                epsilon=epsilon,
                T_space=T_space,
                h_i=h_i,
            )
            - T_in_max
        )

    q_low = 0.0
    f_low = f(q_low)
    if f_low > 0.0:
        return 0.0

    q_high = q_high_init
    f_high = f(q_high)
    expand_iter = 0
    while f_high <= 0.0 and q_high < q_hard_cap and expand_iter < max_expand_iters:
        q_high *= 2.0
        f_high = f(q_high)
        expand_iter += 1

    if f_high <= 0.0:
        return q_high

    for _ in range(max_bisect_iters):
        q_mid = 0.5 * (q_low + q_high)
        f_mid = f(q_mid)
        if abs(f_mid) < tol_abs:
            return q_mid
        if f_mid <= 0.0:
            q_low = q_mid
        else:
            q_high = q_mid

    return 0.5 * (q_low + q_high)

