"""Le module de risque de taux du TSAV 2025 (chapitre 5, sections 5.1.1 et 5.1.2), à la lettre.

Les quatre scénarios prescrits déforment le scénario initial ainsi (5.1.2.1, formules
recopiées de la ligne directrice, rapporté) : les chocs au 90 jours (T ou S) et au 20 ans
(B ou C) sont des fonctions linéaires de la RACINE CARRÉE des taux courants planchers à
0,5 % :

    T± = 0,0049 ± 0,139 rac(max(r_0,25 ; 0,005))
    S± = 0,0039 ± 0,111 rac(max(r_0,25 ; 0,005))
    B± = 0,0028 ± 0,102 rac(max(r_20  ; 0,005))
    C± = 0,0023 ± 0,007 rac(max(r_20  ; 0,005))

entre 0,25 et 20 ans, les COEFFICIENTS s'interpolent linéairement (les polynômes en t de
la ligne directrice) ; de 20 à 70 ans, le taux choqué s'interpole entre le 20 ans choqué
et l'UIR choqué (± 40 pb pour le Canada) ; au-delà, l'UIR choqué. Aucun plancher à zéro.
Scénarios : 1) T-, B-, UIR-40 pb ; 2) S+, C-, UIR-40 pb ; 3) T+, B+, UIR+40 pb ;
4) S-, C+, UIR+40 pb. L'exigence non participante est la pire baisse de valeur nette
(actifs moins passifs) parmi les quatre, plancher à zéro (5.1.2.2-5.1.2.3), sans lissage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lic.curves import UIR, initial_rate, pv

L_UIR = 0.40           # pb -> points de %, choc de l'UIR au Canada (rapporté)

# (pente du coefficient a(t), ordonnée de a(t), pente de c(t), ordonnée de c(t))
_A3 = (0.139468, -0.001873)     # scénarios 1 et 3 : a(t) = 0.139468 - 0.001873 t
_C3 = (0.00492658, -0.00010633)
_A2 = (0.112699, -0.005997)     # scénarios 2 et 4
_C2 = (0.00394084, -0.00008336)

SCENARIOS = {
    1: {"a": _A3, "c": _C3, "signe": -1.0, "uir": -L_UIR},
    2: {"a": _A2, "c": _C2, "signe": +1.0, "uir": -L_UIR},
    3: {"a": _A3, "c": _C3, "signe": +1.0, "uir": +L_UIR},
    4: {"a": _A2, "c": _C2, "signe": -1.0, "uir": +L_UIR},
}


def shock_pct(t: np.ndarray, r_pct: np.ndarray, scenario: int) -> np.ndarray:
    """Le choc (en points de %) aux échéances t <= 20, taux courants r en %."""
    spec = SCENARIOS[scenario]
    t = np.asarray(t, dtype=float)
    a = spec["a"][0] + spec["a"][1] * t
    c = spec["c"][0] + spec["c"][1] * t
    racine = np.sqrt(np.maximum(np.asarray(r_pct, dtype=float) / 100.0, 0.005))
    return (spec["signe"] * a * racine + c) * 100.0


def stressed_rate(curve_row: pd.Series, t: np.ndarray, scenario: int) -> np.ndarray:
    """Le taux comptant choqué (en %) : 0,25-20 ans par les chocs, 20-70 vers l'UIR choqué."""
    t = np.asarray(t, dtype=float)
    r0 = initial_rate(curve_row, t)
    tc = np.clip(t, 0.25, 20.0)
    r_court = r0 + shock_pct(tc, r0, scenario)
    r20 = float(initial_rate(curve_row, np.array([20.0]))[0])
    r20_choque = r20 + float(shock_pct(np.array([20.0]), np.array([r20]), scenario)[0])
    uir_choque = UIR + SCENARIOS[scenario]["uir"]
    milieu = r20_choque + (uir_choque - r20_choque) * (np.clip(t, 20.0, 70.0) - 20.0) / 50.0
    return np.where(t <= 20.0, r_court, np.where(t < 70.0, milieu, uir_choque))


def requirement(actifs: np.ndarray, passifs: np.ndarray, t: np.ndarray,
                curve_row: pd.Series) -> dict[str, float]:
    """L'exigence non participante : pire baisse de la valeur nette parmi les quatre scénarios.

    `actifs` et `passifs` sont des échéanciers de flux positifs aux dates t ; la valeur
    nette vaut PV(actifs) - PV(passifs).
    """
    t = np.asarray(t, dtype=float)
    r0 = initial_rate(curve_row, t)
    net0 = pv(actifs, t, r0) - pv(passifs, t, r0)
    pertes = {}
    for s in SCENARIOS:
        rs = stressed_rate(curve_row, t, s)
        net_s = pv(actifs, t, rs) - pv(passifs, t, rs)
        pertes[f"scenario_{s}"] = net0 - net_s
    pire = max(pertes, key=pertes.get)
    return {**pertes, "pire_scenario": float(pertes[pire]),
            "numero_pire": float(int(pire.split("_")[1])),
            "exigence": max(float(pertes[pire]), 0.0)}
