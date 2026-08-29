"""Le passif stylisé : un bloc fermé de rentes viagères immédiates, mortalité CPM2014.

Bloc déclaré : 10 000 rentiers de 65 ans (hommes), rente de 10 000 $ versée en fin
d'année tant que le rentier vit, aucune participation, aucune valeur de rachat. La
mortalité réalisée égale la mortalité attendue (laboratoire d'ALM : le risque étudié est
le taux, pas la mortalité, déclaré). L'échéancier attendu est figé à la date de départ.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def survival(qx: pd.Series, age0: int) -> np.ndarray:
    """l_t : probabilité d'être vivant à la fin de l'année t (t = 1..115-age0)."""
    q = qx.loc[age0:].to_numpy(dtype=float)
    return np.cumprod(1.0 - q)


def annuity_cashflows(qx: pd.Series, age0: int = 65, n_lives: int = 10_000,
                      benefit: float = 10_000.0) -> tuple[np.ndarray, np.ndarray]:
    """(dates en années, flux attendus en $) d'une rente immédiate de fin d'année."""
    lt = survival(qx, age0)
    t = np.arange(1, len(lt) + 1, dtype=float)
    return t, n_lives * benefit * lt


def zero_coupon_assets(faces: dict[float, float], horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Un portefeuille d'obligations zéro-coupon : {échéance: nominal} -> échéancier annuel."""
    t = np.arange(1, horizon + 1, dtype=float)
    cf = np.zeros_like(t)
    for mat, face in faces.items():
        idx = int(round(mat)) - 1
        if 0 <= idx < len(cf):
            cf[idx] += face
    return t, cf
