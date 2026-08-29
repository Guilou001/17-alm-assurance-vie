"""Trois stratégies d'adossement, du plus grossier au plus fin, et le banc de surplus.

L'immunisation de Redington (1952) : si les actifs égalent le passif en valeur ET en
duration, et que leur convexité est au moins celle du passif, un PETIT déplacement
PARALLÈLE ne peut pas réduire le surplus. La promesse s'arrête là : elle ne dit rien des
déformations de pente, et 2020-2026 en fut une suite. Le banc mesure ce qui reste de la
promesse sur les courbes réelles.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from lic.curves import initial_rate, modified_duration, pv


def _rate(curve_row: pd.Series, t: np.ndarray) -> np.ndarray:
    return initial_rate(curve_row, t)


def duration_match(liab_cf: np.ndarray, t: np.ndarray, curve_row: pd.Series,
                   mat_courte: float = 5.0, mat_longue: float = 25.0,
                   surplus_initial: float = 0.05) -> dict[float, float]:
    """Deux zéro-coupon (barbell) qui égalent (1 + surplus) x PV du passif et sa duration EN DOLLARS.

    Système 2x2 exact sur les valeurs marchandes v_c, v_l :
    v_c + v_l = A ; v_c D_c + v_l D_l = PL x D_passif.

    La deuxième équation apparie la duration en DOLLARS, pas en années. C'est ce que le théorème
    de Redington exige pour protéger le SURPLUS : égaler les durations en années sur un actif qui
    vaut 1,05 fois le passif donne à l'actif une duration en dollars supérieure de 5 %, et le
    surplus garde alors une exposition du PREMIER ordre au déplacement parallèle, le seul cas que
    le théorème couvre. La signature du défaut est nette : à surplus nul la perte est quadratique,
    à surplus de 5 % elle est linéaire. Corrigé le 2026-08-29 après l'audit ; apparier en années
    protège le RATIO actif/passif, pas le surplus en dollars que ce dépôt mesure.
    """
    r = _rate(curve_row, t)
    pl = pv(liab_cf, t, r)
    dl = modified_duration(liab_cf, t, r)
    a = (1.0 + surplus_initial) * pl
    d_c = float(mat_courte / (1.0 + _rate(curve_row, np.array([mat_courte]))[0] / 100.0))
    d_l = float(mat_longue / (1.0 + _rate(curve_row, np.array([mat_longue]))[0] / 100.0))
    v_l = (pl * dl - a * d_c) / (d_l - d_c)
    v_c = a - v_l
    if v_c < 0 or v_l < 0:
        raise ValueError("barbell impossible : la duration du passif sort de l'intervalle")
    # valeurs marchandes -> nominaux : face = valeur / facteur d'actualisation
    df_c = (1.0 + _rate(curve_row, np.array([mat_courte]))[0] / 100.0) ** (-mat_courte)
    df_l = (1.0 + _rate(curve_row, np.array([mat_longue]))[0] / 100.0) ** (-mat_longue)
    return {mat_courte: v_c / df_c, mat_longue: v_l / df_l}


def bucket_match(liab_cf: np.ndarray, t: np.ndarray, curve_row: pd.Series,
                 noeuds: tuple[float, ...] = (1.0, 2.0, 5.0, 10.0, 20.0, 30.0),
                 surplus_initial: float = 0.05) -> dict[float, float]:
    """L'appariement par taux clés : chaque flux du passif est réparti sur les deux nœuds
    voisins au prorata inverse de la distance (triangulaire), en VALEUR actualisée ; les
    zéro-coupon des nœuds portent alors les mêmes sensibilités par taux clés que le passif."""
    r = _rate(curve_row, t)
    df = (1.0 + r / 100.0) ** (-t)
    valeurs = {k: 0.0 for k in noeuds}
    for ti, cfi, dfi in zip(t, liab_cf, df, strict=True):
        v = cfi * dfi
        if ti <= noeuds[0]:
            valeurs[noeuds[0]] += v
        elif ti >= noeuds[-1]:
            valeurs[noeuds[-1]] += v
        else:
            j = np.searchsorted(noeuds, ti)
            lo, hi = noeuds[j - 1], noeuds[j]
            w_hi = (ti - lo) / (hi - lo)
            valeurs[lo] += v * (1.0 - w_hi)
            valeurs[hi] += v * w_hi
    # le surplus est logé au nœud LE PLUS COURT et non réparti au prorata : le multiplier partout
    # donnerait à l'actif des sensibilités par taux clés supérieures de 5 % à celles du passif, donc
    # une exposition du premier ordre du surplus, exactement le défaut corrigé dans duration_match
    valeurs[noeuds[0]] += surplus_initial * sum(valeurs.values())
    faces = {}
    for k, v in valeurs.items():
        df_k = (1.0 + _rate(curve_row, np.array([k]))[0] / 100.0) ** (-k)
        faces[k] = v / df_k
    return faces


def cash_strategy(liab_cf: np.ndarray, t: np.ndarray, curve_row: pd.Series,
                  surplus_initial: float = 0.05) -> dict[float, float]:
    """Le contre-exemple : tout l'actif en zéro-coupon UN AN, aucune immunisation."""
    r = _rate(curve_row, t)
    a = (1.0 + surplus_initial) * pv(liab_cf, t, r)
    df1 = (1.0 + _rate(curve_row, np.array([1.0]))[0] / 100.0) ** (-1.0)
    return {1.0: a / df1}


def surplus_path(liab_cf: np.ndarray, t: np.ndarray, monthly_curves: pd.DataFrame,
                 strategie) -> pd.Series:
    """Le surplus mois par mois, autofinancé : aucun apport, aucune sortie hors rentes dues.

    Chaque mois : (1) les zéro-coupon du mois précédent sont revalorisés sur la courbe du
    jour, leurs échéances raccourcies d'un douzième, ceux qui échoient rendent le pair ;
    (2) les rentes devenues dues pendant le mois sont PAYÉES, en déduction de l'actif ;
    (3) le passif restant est revalorisé, son échéancier raccourci d'autant ; (4) l'actif
    est réinvesti selon la stratégie (seuls ses poids relatifs comptent, l'échelle est
    ramenée à la valeur d'actif courante).
    """
    from lic.curves import discount

    dates = monthly_curves.index
    surplus = {}
    faces_prev: dict[float, float] | None = None
    for i, d in enumerate(dates):
        row = monthly_curves.loc[d]
        ecoule = i / 12.0
        t_liab = t - ecoule
        vivant = t_liab > 1e-9
        r_liab = initial_rate(row, t_liab[vivant])
        pl = pv(liab_cf[vivant], t_liab[vivant], r_liab)
        if faces_prev is None:
            a_val = (1.0 + 0.05) * pl                     # surplus initial de 5 % (précepte)
        else:
            a_val = 0.0
            for mat, face in faces_prev.items():
                m = mat - 1.0 / 12.0                      # un mois s'est écoulé
                if m <= 1e-9:
                    a_val += face                         # le zéro échu rend le pair
                else:
                    rr = initial_rate(row, np.array([m]))[0]
                    a_val += face * float(discount(np.array([rr]), np.array([m]))[0])
            dues = float(liab_cf[(t - (i - 1) / 12.0 > 1e-9) & (t - ecoule <= 1e-9)].sum())
            a_val -= dues                                 # les rentes échues sont payées
        surplus[d] = a_val - pl
        faces_cibles = strategie(liab_cf[vivant], t_liab[vivant], row)
        total_cible = 0.0
        for mat, face in faces_cibles.items():
            rr = initial_rate(row, np.array([mat]))[0]
            total_cible += face * float(discount(np.array([rr]), np.array([mat]))[0])
        echelle = a_val / total_cible
        faces_prev = {m: f * echelle for m, f in faces_cibles.items()}
    return pd.Series(surplus)
