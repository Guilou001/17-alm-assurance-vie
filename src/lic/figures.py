"""Trois figures : le passif, le surplus à travers 2020-2026, l'exigence TSAV contre le réalisé."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from gvf.style import OKABE_ITO, appliquer, formateur  # noqa: F401

# La palette et les réglages viennent de la couche partagée du portefeuille : les mêmes
# couleurs et la même virgule décimale dans tous les dépôts, corrigées à un seul endroit.


def use_style():
    """Les réglages communs, puis le formateur d'axe en français."""
    appliquer()
    return formateur()


def _mm(v: float) -> str:
    return f"{v / 1e6:,.1f}".replace(",", " ").replace(".", ",")


def fig_liability(t: np.ndarray, cf: np.ndarray, duration: float, dest: Path) -> None:
    """L'échéancier du bloc de rentes : long, décroissant, duration proche de dix ans."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(8.8, 4.2))
    ax.bar(t, cf / 1e6, color=OKABE_ITO[0], width=0.85)
    ax.axvline(duration, color=OKABE_ITO[3], linestyle="--", linewidth=1.4,
               label=f"duration modifiée : {duration:.1f} ans".replace(".", ","))
    ax.set_xlabel("Années depuis le départ (rentiers de 65 ans, CPM2014)")
    ax.set_ylabel("Rentes versées dans l'année\n(M$ nominaux, non actualisés)", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.xaxis.set_major_formatter(fr)
    ax.legend(fontsize=9)
    ax.set_title("Un bloc de rentes est une obligation dont les coupons meurent avec les rentiers")
    fig.savefig(dest)
    plt.close(fig)


def fig_surplus(paths: dict[str, pd.Series], dest: Path) -> None:
    """Le surplus des trois stratégies à travers le choc de taux 2020-2026."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    for (name, s), color in zip(paths.items(), OKABE_ITO, strict=False):
        ax.plot(s.index, s.to_numpy() / 1e6, color=color,
                label=f"{name} : creux {_mm(float(s.min()))}, "
                      f"au {s.index[-1]:%Y-%m-%d} {_mm(float(s.iloc[-1]))} M\\$")
    ax.axhline(0, color="0.3", linewidth=0.9)
    ax.axvspan(pd.Timestamp("2022-03-01"), pd.Timestamp("2023-12-31"), color="0.90", zorder=0)
    ax.text(pd.Timestamp("2022-04-01"), ax.get_ylim()[1] * 0.95, "hausse de 2022-23",
            fontsize=8.5, color="0.4", va="top")
    ax.set_ylabel("Surplus : actif moins passif\n(millions de dollars)", fontsize=9.5)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=8.5, loc="best")
    # le titre nomme les nombres qu'il affirme, tous lus dans les trajectoires tracées
    depart = {n: float(s.iloc[0]) for n, s in paths.items()}
    arrivee = {n: float(s.iloc[-1]) for n, s in paths.items()}
    cles = next((n for n in paths if "clés" in n), list(paths)[1])
    dur = next((n for n in paths if "uration" in n), list(paths)[0])
    creux = {n: float(s.min()) for n, s in paths.items()}
    ax.set_title(f"Le livre par taux clés tient le surplus : {_mm(depart[cles])} au départ, creux à "
                 f"{_mm(creux[cles])}, {_mm(arrivee[cles])} M\\$ à l\'arrivée\nla duration seule "
                 f"dérive de {_mm(abs(arrivee[dur] - depart[dur]))} M\\$ sur "
                 f"{len(next(iter(paths.values())))} mois", fontsize=11)
    fig.savefig(dest)
    plt.close(fig)


def fig_licat(pertes: dict[str, float], exigence: float, perte_realisee: float,
              date_calcul: str, dest: Path) -> None:
    """Les quatre scénarios du TSAV contre la pire perte réalisée du banc."""
    fr = use_style()
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    # un numéro de scénario ne dit rien au lecteur : chaque barre porte la déformation prescrite
    formes = {1: "tout baisse", 2: "aplatissement", 3: "tout monte", 4: "pentification"}
    noms = [f"scénario {i}\n{formes[i]}" for i in range(1, 5)]
    vals = [pertes[f"scenario_{i}"] / 1e6 for i in range(1, 5)]
    colors = [OKABE_ITO[3] if v == max(vals) else OKABE_ITO[0] for v in vals]
    ax.bar(noms, vals, color=colors, width=0.55)
    lim = max(abs(v) for v in vals) * 1.35
    ax.set_ylim(-lim, max(lim, perte_realisee / 1e6 * 1.15))
    for n, v in zip(noms, vals, strict=True):
        ax.text(n, v + (0.4 if v >= 0 else -0.4), f"{v:+.1f}".replace(".", ","),
                ha="center", va="bottom" if v >= 0 else "top", fontsize=9)
    ax.axhline(perte_realisee / 1e6, color=OKABE_ITO[2], linestyle="--", linewidth=1.6,
               label=f"pire baisse de surplus sur les 18 mois suivants, après rebalancements\net rentes payées ({_mm(perte_realisee)} M$, mesuré)")
    ax.axhline(0, color="0.3", linewidth=0.9)
    ax.set_ylabel("Variation de la valeur nette du livre apparié\nen duration, actif moins passif "
                  "(M$ ; positif = perte)", fontsize=9)
    ax.yaxis.set_major_formatter(fr)
    ax.legend(fontsize=9)
    ax.set_title(f"Exigence TSAV au {date_calcul} : {_mm(exigence)} M$, choc instantané, "
                 f"pire des quatre scénarios", fontsize=11.5)
    fig.savefig(dest)
    plt.close(fig)
