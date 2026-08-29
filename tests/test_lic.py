"""Redington en forme fermée, les chocs du chapitre 5 à la main, les identités d'actualisation."""

import numpy as np
import pandas as pd
import pytest

from lic.curves import UIR, convexity, discount, initial_rate, modified_duration, pv
from lic.immunize import bucket_match, cash_strategy, duration_match
from lic.liability import annuity_cashflows, survival, zero_coupon_assets
from lic.licat import requirement, shock_pct, stressed_rate

TAUS = np.arange(0.25, 30.25, 0.25)


def _flat(rate: float = 4.0) -> pd.Series:
    return pd.Series(rate, index=TAUS)


def _qx_constant(q: float = 0.05) -> pd.Series:
    return pd.Series(q, index=range(18, 116))


def test_initial_curve_structure():
    row = _flat(3.0)
    t = np.array([1.0, 20.0, 45.0, 70.0, 90.0])
    r = initial_rate(row, t)
    assert r[0] == pytest.approx(3.0) and r[1] == pytest.approx(3.0)
    assert r[2] == pytest.approx(3.0 + (UIR - 3.0) * 0.5)     # 45 ans : mi-chemin vers l'UIR
    assert r[3] == pytest.approx(UIR) and r[4] == pytest.approx(UIR)


def test_zero_coupon_duration_annual_compounding():
    row = _flat(4.0)
    t = np.array([7.0])
    cf = np.array([100.0])
    d = modified_duration(cf, t, initial_rate(row, t))
    assert d == pytest.approx(7.0 / 1.04, rel=1e-4)           # D_mod = t/(1+r), forme fermée


def test_annuity_pv_closed_form_constant_mortality():
    # q constant : PV = B somme ((1-q)/(1+r))^t, série géométrique fermée
    q, r, n = 0.05, 0.04, 98 - 0
    qx = _qx_constant(q)
    t, cf = annuity_cashflows(qx, age0=65, n_lives=1, benefit=1.0)
    x = (1 - q) / (1 + r)
    attendu = x * (1 - x ** len(t)) / (1 - x)
    calc = pv(cf, t, np.full(len(t), 100.0 * r))
    assert calc == pytest.approx(attendu, rel=1e-10)
    _ = n


def test_survival_is_a_product():
    qx = _qx_constant(0.1)
    lt = survival(qx, 65)
    assert lt[0] == pytest.approx(0.9) and lt[2] == pytest.approx(0.9**3)


def test_licat_shock_hand_values():
    # r = 4 % : racine de 0,04 = 0,2 ; T+ = 0,0049 + 0,139 x 0,2 = 0,0327, en points : 3,27
    s = shock_pct(np.array([0.25]), np.array([4.0]), scenario=3)
    assert s[0] == pytest.approx(3.27, abs=0.03)
    s1 = shock_pct(np.array([0.25]), np.array([4.0]), scenario=1)
    assert s1[0] == pytest.approx(0.49 - 2.78, abs=0.03)      # T- = 0,0049 - 0,139 rac(r)
    # au 20 ans, scénario 3 : B+ = 0,0028 + 0,102 x 0,2
    s20 = shock_pct(np.array([20.0]), np.array([4.0]), scenario=3)
    assert s20[0] == pytest.approx(0.28 + 2.04, abs=0.05)


def test_licat_floor_on_rate():
    # sous 0,5 %, la racine est plancherisée : le choc ne dépend plus du taux
    a = shock_pct(np.array([0.25]), np.array([0.2]), scenario=3)
    b = shock_pct(np.array([0.25]), np.array([0.5]), scenario=3)
    assert a[0] == pytest.approx(b[0], abs=1e-9)


def test_stressed_rate_uir_shift():
    row = _flat(3.0)
    t = np.array([80.0])
    assert stressed_rate(row, t, 3)[0] == pytest.approx(UIR + 0.40)
    assert stressed_rate(row, t, 1)[0] == pytest.approx(UIR - 0.40)


def test_requirement_floors_at_zero_when_hedged():
    # actifs = passifs, flux identiques : aucune perte possible, exigence nulle
    row = _flat(3.5)
    t = np.arange(1.0, 31.0)
    cf = np.full(30, 10.0)
    req = requirement(cf, cf.copy(), t, row)
    assert req["exigence"] == pytest.approx(0.0, abs=1e-9)


def test_redington_wide_barbell_survives_parallel_shocks():
    # le théorème exige duration appariée ET convexité d'actif superieure : le barbell LARGE
    # (2-30 ans) remplit les deux conditions et ne peut pas perdre sous un choc parallèle
    row = _flat(4.0)
    qx = _qx_constant(0.04)
    t, cf = annuity_cashflows(qx, n_lives=100, benefit=1000.0)
    r = initial_rate(row, t)
    faces = duration_match(cf, t, row, mat_courte=2.0, mat_longue=30.0, surplus_initial=0.0)
    t_a, cf_a = zero_coupon_assets(faces, int(t.max()))
    conv_a = convexity(cf_a, t_a, initial_rate(row, t_a))
    conv_l = convexity(cf, t, r)
    assert conv_a > conv_l                                    # condition de Redington remplie
    for bump in (-1.0, 1.0, -0.5, 0.5):
        s = pv(cf_a, t_a, initial_rate(row, t_a) + bump) - pv(cf, t, r + bump)
        assert s >= -1e-6                                     # jamais de perte au second ordre


def test_narrow_barbell_violates_redington_condition():
    # le barbell 5-25 du banc a MOINS de convexité que le passif à longue queue : la
    # promesse de Redington ne le couvre pas, et c'est le défaut que le banc mesure
    row = _flat(4.0)
    qx = _qx_constant(0.04)
    t, cf = annuity_cashflows(qx, n_lives=100, benefit=1000.0)
    faces = duration_match(cf, t, row, surplus_initial=0.0)
    t_a, cf_a = zero_coupon_assets(faces, int(t.max()))
    conv_a = convexity(cf_a, t_a, initial_rate(row, t_a))
    conv_l = convexity(cf, t, initial_rate(row, t))
    assert conv_a < conv_l


def test_duration_match_is_exact():
    row = _flat(3.0)
    qx = _qx_constant(0.05)
    t, cf = annuity_cashflows(qx, n_lives=10, benefit=100.0)
    faces = duration_match(cf, t, row, surplus_initial=0.05)
    t_a, cf_a = zero_coupon_assets(faces, int(t.max()))
    r_l, r_a = initial_rate(row, t), initial_rate(row, t_a)
    assert pv(cf_a, t_a, r_a) == pytest.approx(1.05 * pv(cf, t, r_l), rel=1e-9)
    assert modified_duration(cf_a, t_a, r_a) == pytest.approx(modified_duration(cf, t, r_l), rel=1e-3)


def test_bucket_match_preserves_value():
    row = _flat(3.0)
    qx = _qx_constant(0.05)
    t, cf = annuity_cashflows(qx, n_lives=10, benefit=100.0)
    faces = bucket_match(cf, t, row, surplus_initial=0.0)
    t_a, cf_a = zero_coupon_assets(faces, int(max(faces) + 1))
    assert pv(cf_a, t_a, initial_rate(row, t_a)) == pytest.approx(pv(cf, t, initial_rate(row, t)), rel=5e-3)


def test_cash_strategy_all_in_one_year():
    row = _flat(3.0)
    qx = _qx_constant(0.05)
    t, cf = annuity_cashflows(qx, n_lives=10, benefit=100.0)
    faces = cash_strategy(cf, t, row)
    assert list(faces) == [1.0]


def test_discount_identity():
    assert discount(np.array([4.0]), np.array([2.0]))[0] == pytest.approx(1.04**-2, rel=1e-12)
