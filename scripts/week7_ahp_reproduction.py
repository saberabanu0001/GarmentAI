#!/usr/bin/env python3
"""
Reproduce AHP numbers in docs/Week7-Design-Evaluation-AHP-Report.md

Method:
  - Principal eigenvector approximated by power iteration (no numpy).
  - Consistency ratio CR = CI / RI, CI = (lambda_max - n) / (n - 1).

Run from repo root:
  python3 scripts/week7_ahp_reproduction.py
"""

from __future__ import annotations

# Saaty random index
RI = {3: 0.58, 4: 0.90, 5: 1.12, 6: 1.24, 7: 1.32, 8: 1.41}


def fill_reciprocal(upper: list[list[float]]) -> list[list[float]]:
    """Build full matrix from upper triangle (including diagonal)."""
    n = len(upper)
    m = [[0.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            if j >= i:
                m[i][j] = float(upper[i][j])
            else:
                m[i][j] = 1.0 / m[j][i]
    return m


def power_method_priority(A: list[list[float]], iterations: int = 200) -> tuple[list[float], float]:
    """Approximate principal eigenvector; return (normalized weights, lambda_max approx)."""
    n = len(A)
    v = [1.0] * n
    for _ in range(iterations):
        nv = [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]
        mx = max(abs(x) for x in nv)
        v = [x / mx for x in nv]
    s = sum(v)
    w = [x / s for x in v]
    av = [sum(A[i][j] * v[j] for j in range(n)) for i in range(n)]
    lam = sum(av[i] / v[i] for i in range(n)) / n
    return w, lam


def consistency_ratio(A: list[list[float]], lam: float) -> float:
    n = len(A)
    ci = (lam - n) / (n - 1) if n > 1 else 0.0
    return ci / RI[n]


def main() -> None:
    labels_c = [
        "Accuracy",
        "Interpretability",
        "Reliability",
        "Cost",
        "Privacy",
        "Feasibility",
    ]

    # Criteria matrix (upper triangle rows 0..5) — matches report §4.2
    C = fill_reciprocal(
        [
            [1, 2, 1, 2, 2, 4],
            [0, 1, 0.5, 2, 2, 4],
            [0, 0, 1, 3, 3, 4],
            [0, 0, 0, 1, 1, 3],
            [0, 0, 0, 0, 1, 3],
            [0, 0, 0, 0, 0, 1],
        ]
    )

    w_c, lam_c = power_method_priority(C)
    cr_c = consistency_ratio(C, lam_c)

    print("=== Criteria weights (order:", ", ".join(labels_c), ") ===")
    for lab, val in zip(labels_c, w_c):
        print(f"  {lab:22s}  {val:.6f}")
    print(f"lambda_max (approx)  {lam_c:.6f}")
    print(f"CR (criteria)        {cr_c:.6f}  (acceptable if < 0.10)\n")

    # Alternative matrices A,B,C = Local, Hybrid, Cloud — matches report §5
    upper_matrices: list[list[list[float]]] = [
        [[1, 0.5, 1 / 3], [0, 1, 0.5], [0, 0, 1]],  # Accuracy
        [[1, 1, 2], [0, 1, 2], [0, 0, 1]],  # Interpretability
        [[1, 1, 2], [0, 1, 2], [0, 0, 1]],  # Reliability
        [[1, 1, 3], [0, 1, 3], [0, 0, 1]],  # Cost
        [[1, 1, 3], [0, 1, 3], [0, 0, 1]],  # Privacy
        [[1, 0.5, 1], [0, 1, 2], [0, 0, 1]],  # Feasibility
    ]

    alt_labels = ["A Local-first", "B Hybrid", "C Cloud-centric"]
    local_weights: list[list[float]] = []

    print("=== Alternative local priorities (rows A,B,C) ===")
    for lab, up in zip(labels_c, upper_matrices):
        M = fill_reciprocal(up)
        w_a, lam_a = power_method_priority(M)
        cr_a = consistency_ratio(M, lam_a)
        local_weights.append(w_a)
        ws = ", ".join(f"{alt_labels[i]}={w_a[i]:.6f}" for i in range(3))
        print(f"{lab:22s}  {ws}   CR={cr_a:.6f}")

    print("\n=== Global priorities (synthesis) ===")
    g = [0.0, 0.0, 0.0]
    for wi, ua in zip(w_c, local_weights):
        for k in range(3):
            g[k] += wi * ua[k]
    for i in range(3):
        print(f"  {alt_labels[i]:16s}  {g[i]:.6f}  ({g[i]*100:.2f}%)")

    order = sorted(range(3), key=lambda k: -g[k])
    print("\nRanking:", " > ".join(alt_labels[k] for k in order))


if __name__ == "__main__":
    main()
