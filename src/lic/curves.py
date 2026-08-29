"""La structure de taux du TSAV et les calculs d'actualisation, en composition annuelle.

Le chapitre 5 (section 5.1.1) construit le scénario initial ainsi : taux comptant publiés
jusqu'à 20 ans, interpolation LINÉAIRE DU TAUX entre le 20 ans et le taux ultime (UIR,
4,5 % pour le Canada) de 20 à 70 ans, UIR constant au-delà. Toute l'actualisation du dépôt
suit cette structure et la composition annuelle : facteur (1 + r_t)^(-t).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

UIR = 4.5              # % , Canada (TSAV 5.1.1, rapporté)


def initial_rate(curve_row: pd.Series, t: np.ndarray) -> np.ndarray:
    """Le taux comptant du scénario initial (en %) aux échéances t (années)."""
    taus = np.array(curve_row.index, dtype=float)
    vals = curve_row.to_numpy(dtype=float)
    t = np.asarray(t, dtype=float)
    r20 = float(np.interp(20.0, taus, vals))
    court = np.interp(np.clip(t, taus[0], 20.0), taus, vals)
    milieu = r20 + (UIR - r20) * (np.clip(t, 20.0, 70.0) - 20.0) / 50.0
    return np.where(t <= 20.0, court, np.where(t < 70.0, milieu, UIR))


def discount(rates_pct: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Facteurs d'actualisation en composition annuelle."""
    return (1.0 + np.asarray(rates_pct, dtype=float) / 100.0) ** (-np.asarray(t, dtype=float))


def pv(cashflows: np.ndarray, t: np.ndarray, rates_pct: np.ndarray) -> float:
    """La valeur actualisée d'un échéancier sur la structure donnée."""
    return float(np.sum(np.asarray(cashflows, dtype=float) * discount(rates_pct, t)))


def modified_duration(cashflows: np.ndarray, t: np.ndarray, rates_pct: np.ndarray,
                      bump_bp: float = 1.0) -> float:
    """Sensibilité au déplacement parallèle, par revalorisation à ± bump_bp."""
    p0 = pv(cashflows, t, rates_pct)
    up = pv(cashflows, t, rates_pct + bump_bp / 100.0)
    dn = pv(cashflows, t, rates_pct - bump_bp / 100.0)
    return float((dn - up) / (2.0 * p0 * bump_bp / 10000.0))


def convexity(cashflows: np.ndarray, t: np.ndarray, rates_pct: np.ndarray,
              bump_bp: float = 10.0) -> float:
    """Convexité numérique : (P+ + P- - 2 P0) / (P0 dy^2)."""
    p0 = pv(cashflows, t, rates_pct)
    dy = bump_bp / 10000.0
    up = pv(cashflows, t, rates_pct + bump_bp / 100.0)
    dn = pv(cashflows, t, rates_pct - bump_bp / 100.0)
    return float((up + dn - 2.0 * p0) / (p0 * dy * dy))
