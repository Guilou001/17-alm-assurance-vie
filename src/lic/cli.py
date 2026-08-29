"""Ligne de commande : télécharger, puis dérouler le laboratoire ALM complet."""

from __future__ import annotations

from pathlib import Path

import typer

app = typer.Typer(help="ALM d'assurance vie sous le TSAV : bloc de rentes CPM2014, immunisation "
                       "de Redington, banc de surplus 2019-2026, module de risque de taux du "
                       "chapitre 5 recalculé à la main.")


@app.callback()
def main() -> None:
    """Sous-commandes nommées."""


@app.command()
def fetch() -> None:
    """Courbe zéro-coupon BdC et table CPM2014 de l'ICA."""
    from lic import data

    data.fetch()
    curve = data.load_curve()
    qx = data.load_mortality()
    typer.echo(f"courbe : {len(curve)} jours -> {curve.index[-1].date()} ; "
               f"CPM2014 : âges {qx.index[0]}-{qx.index[-1]}, q65 = {qx.loc[65]:.5f}")


@app.command()
def lab(out: Path = Path("results"), debut: str = "2019-12", fin: str = "2026-08") -> None:
    """Passif, immunisations, banc de surplus mensuel, exigence TSAV, trois figures."""
    import numpy as np
    import pandas as pd

    from lic import data, figures, immunize, liability, licat
    from lic.curves import convexity, initial_rate, modified_duration, pv

    curve = data.load_curve()
    monthly = curve.resample("ME").last().dropna(how="all").loc[debut:fin]
    monthly.index = monthly.index.normalize()
    qx = data.load_mortality()
    t, cf = liability.annuity_cashflows(qx)

    tables, figs = out / "tables", out / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figs.mkdir(parents=True, exist_ok=True)

    row0 = monthly.iloc[0]
    r0 = initial_rate(row0, t)
    pl0 = pv(cf, t, r0)
    dl0 = modified_duration(cf, t, r0)
    cl0 = convexity(cf, t, r0)
    pd.DataFrame([{"pv_passif": pl0, "duration_modifiee": dl0, "convexite": cl0,
                   "date": str(monthly.index[0].date()), "somme_rentes": float(cf.sum())}]
                 ).round(3).to_csv(tables / "passif.csv", index=False)
    figures.fig_liability(t, cf, dl0, figs / "passif.png")

    strategies = {
        "duration seule (barbell 5-25)": immunize.duration_match,
        "taux clés (6 nœuds)": immunize.bucket_match,
        "aucune (tout à 1 an)": immunize.cash_strategy,
    }
    paths = {}
    for name, strat in strategies.items():
        paths[name] = immunize.surplus_path(cf, t, monthly, strat)
    pd.DataFrame(paths).round(0).to_csv(tables / "surplus_mensuel.csv")
    figures.fig_surplus(paths, figs / "surplus.png")

    # l'exigence TSAV au 2021-12, la veille du choc : actifs = barbell duration
    d_calc = monthly.loc[:"2021-12"].index[-1]
    row_calc = monthly.loc[d_calc]
    ecoule = float(monthly.index.get_loc(d_calc)) / 12.0
    t_c = t - ecoule
    viv = t_c > 1e-9
    faces = immunize.duration_match(cf[viv], t_c[viv], row_calc)
    # l'actif du module est ramené à la valeur que le banc détient réellement à cette date
    r_calc = initial_rate(row_calc, t_c[viv])
    pl_calc = pv(cf[viv], t_c[viv], r_calc)
    s_dur_calc = float(paths["duration seule (barbell 5-25)"].loc[d_calc])
    echelle = (pl_calc + s_dur_calc) / ((1.0 + 0.05) * pl_calc)
    faces = {m: f * echelle for m, f in faces.items()}
    horizon = int(np.ceil(t_c[viv].max()))
    t_a, cf_a = liability.zero_coupon_assets(faces, horizon)
    # échéanciers sur la même grille pour le module : actifs zéro-coupon, passif attendu
    grille = np.union1d(t_a, t_c[viv])
    a_g = np.zeros_like(grille)
    p_g = np.zeros_like(grille)
    for tt, v in zip(t_a, cf_a, strict=True):
        a_g[np.searchsorted(grille, tt)] += v
    for tt, v in zip(t_c[viv], cf[viv], strict=True):
        p_g[np.isclose(grille, tt)] += v
    # l'actif est d'abord ramené à (1,05 x passif) sur la courbe de calcul (même échelle que le banc)
    req = licat.requirement(a_g, p_g, grille, row_calc)
    pd.DataFrame([req]).round(1).to_csv(tables / "exigence_licat.csv", index=False)

    s_dur = paths["duration seule (barbell 5-25)"]
    apres = s_dur.loc[d_calc:]
    perte_realisee = float(s_dur.loc[d_calc] - apres.min())
    figures.fig_licat({k: v for k, v in req.items() if k.startswith("scenario")},
                      req["exigence"], perte_realisee, str(d_calc.date()), figs / "licat.png")
    pd.DataFrame([{"date_calcul": str(d_calc.date()), "perte_realisee": perte_realisee,
                   "exigence": req["exigence"], "couverture": req["exigence"] / max(perte_realisee, 1e-9)}]
                 ).round(3).to_csv(tables / "exigence_vs_realise.csv", index=False)

    typer.echo(f"passif au départ : {pl0 / 1e6:.1f} M$, duration {dl0:.2f} ans, convexité {cl0:.1f}")
    for name, s in paths.items():
        typer.echo(f"  surplus {name} : départ {s.iloc[0] / 1e6:+.1f}, min {s.min() / 1e6:+.1f}, "
                   f"fin {s.iloc[-1] / 1e6:+.1f} M$")
    typer.echo(f"exigence TSAV au {d_calc.date()} : {req['exigence'] / 1e6:.1f} M$ "
               f"(pire scénario : {int(req['numero_pire'])}) ; "
               f"pire perte réalisée ensuite : {perte_realisee / 1e6:.1f} M$")


if __name__ == "__main__":
    app()
