# L'immunisation à l'épreuve de 2022, et le capital TSAV à l'épreuve du réalisé

Un bloc de rentes viagères (mortalité CPM2014), trois stratégies d'adossement sur les
courbes zéro-coupon réelles de 2019 à 2026, et le module de risque de taux du TSAV 2025
recalculé à la lettre depuis la ligne directrice de l'OSFI. *English summary below.*

## En bref

1. **À taux plancher, les chocs prescrits du TSAV étaient petits, et 2022 les a enfoncés.**
   Les chocs du chapitre 5 sont des fonctions de la RACINE CARRÉE des taux courants : fin
   2021, avec un 90 jours sous 0,5 %, le plus fort choc court prescrit parmi les quatre
   scénarios (le T+ du scénario « tout monte ») n'était que de +147 pb ; 2022-23 en a
   livré +513 (mesuré). Résultat : l'exigence calculée au 2021-12 vaut 7,4 M$, fixée par
   le scénario 1 (tout baisse), et la perte ensuite réalisée par le livre apparié en
   duration vaut 7,9 M$ : une couverture de 93,5 % (mesuré,
   `results/tables/exigence_vs_realise.csv`). Ce n'est pas la duration qui laisse passer
   la perte, c'est la CONVEXITÉ : le barbell 5-25 en a moins que le passif à queue de
   cinquante ans, si bien que le surplus baisse au second ordre dans les deux directions,
   et davantage quand les taux baissent. (Mesuré ; formules rapportées de la ligne
   directrice, section 5.1.2.1.)
2. **Redington tient exactement là où son théorème s'applique, et pas un pas plus loin.**
   Duration appariée ET convexité d'actif supérieure : aucun choc parallèle ne peut
   entamer le surplus (testé en forme fermée sur un barbell large). Mais le barbell 5-25
   du banc viole la condition de convexité face à un passif à queue de 50 ans (testé), et
   le théorème ne dit de toute façon rien des déformations de pente, qui ont fait
   l'essentiel de 2020-2026. (Mesuré et testé.)
3. **Le banc de 81 mois départage les trois stratégies sans appel.** L'appariement par
   taux clés tient le surplus (81,3 M$ au départ, creux à 77,3, arrivée à 92,5 M$ : un
   surplus immunisé s'accroît au taux sans risque, il ne dérive pas) ; la duration seule
   le laisse errer (creux à 71,3, arrivée à 110,9 M$, et l'arrivée haute est une chance de
   trajectoire, pas un mérite) ; l'absence de couverture le fait passer par
   l'INSOLVABILITÉ (-101,8 M$ en juillet 2020) avant de finir à +329 M$ : les deux queues
   du même risque non couvert. (Mesuré.)

## La question

L'immunisation par la durée promet un surplus insensible aux taux, et le TSAV, le test de
capital des assureurs vie canadiens, tarifie le risque de taux par quatre scénarios
prescrits. Or entre 2020 et 2023 la courbe canadienne ne s'est pas déplacée : elle s'est
TORDUE, l'écart 10 ans moins 3 mois passant de +198 pb (25 mars 2022) à -212 pb
(27 décembre 2023), en composition annuelle, la convention du dépôt. Que reste-t-il de la
promesse de l'immunisation, et le capital prescrit couvrait-il la perte réellement subie ?

## Les données (100 % libres, téléchargées par script, jamais commitées)

| Source | Contenu | Usage | Statut |
|---|---|---|---|
| Banque du Canada, courbe zéro-coupon | 120 maturités quotidiennes, convertie en composition annuelle | valorisation et banc mensuel 2019-12 à 2026-08 | mesuré |
| ICA, table CPM2014 | mortalité des retraités canadiens, générationnelle 1999-2013 (CPM-B incorporée) | colonne 2013 en table STATIQUE (précepte déclaré) | mesuré |
| OSFI, TSAV 2025, chapitre 5 | formules des scénarios de taux (5.1.1-5.1.2.3) | recopiées à la lettre du PDF officiel | rapporté |

Le passif : 10 000 rentiers de 65 ans (hommes, déclaré), rente de 10 000 $ en fin d'année,
bloc fermé, non participant, sans rachat. Au 2019-12 : valeur actualisée de 1 625,5 M$ pour
2 018 M$ de rentes attendues, duration modifiée de 10,88 ans, convexité de 182 (mesuré,
`results/tables/passif.csv`). La mortalité réalisée égale l'attendue : le laboratoire
isole le risque de TAUX, déclaré.

![Passif](results/figures/passif.png)

**Comment lire cette figure.** Les rentes attendues année par année : un bloc de rentes
est une obligation dont les coupons meurent avec les rentiers, d'où cette décrue régulière
sur cinquante ans et une duration proche de onze ans, hors de portée de la plupart des
obligations simples.

## Volet 1 : le module de taux du TSAV, à la lettre

La structure initiale (section 5.1.1, rapporté) : taux comptant publiés jusqu'à 20 ans,
interpolation linéaire du taux vers le taux ultime (UIR, 4,5 % pour le Canada) entre 20 et
70 ans, UIR au-delà. C'est la composante SANS RISQUE de 5.1.1 : la même section prescrit
aussi un écart d'actualisation (90 % de l'écart d'un indice obligataire corporatif de 0 à
20 ans, écart ultime de 80 pb, donc une actualisation ultime de 5,3 %) que le laboratoire
OMET, l'actualisation se faisant au sans-risque pur (déclaré ; le niveau du passif en
dépend, pas la mécanique des chocs). Les quatre scénarios (5.1.2.1) déforment cette structure par des
chocs au 90 jours (T ou S) et au 20 ans (B ou C), fonctions linéaires de la racine carrée
des taux planchers à 0,5 % :

```
T± = 0,0049 ± 0,139 rac(max(r_0,25 ; 0,005))      S± = 0,0039 ± 0,111 rac(...)
B± = 0,0028 ± 0,102 rac(max(r_20  ; 0,005))       C± = 0,0023 ± 0,007 rac(...)
```

avec interpolation linéaire des coefficients entre 0,25 et 20 ans (les polynômes en t de
la ligne directrice, recopiés), UIR choqué de ± 40 pb, aucun plancher à zéro. Scénario 1 :
tout baisse ; 2 : le court monte, le long à peine (aplatissement) ; 3 : tout monte ; 4 :
le court baisse, le long monte (pentification). L'exigence non participante est la pire
baisse de valeur nette parmi les quatre, plancher à zéro, sans lissage (5.1.2.2-5.1.2.3).
Le test `test_licat_shock_hand_values` refait les chocs à la main : à 4 %, T+ = 0,0049 +
0,139 x 0,2 = +327 pb, exactement.

## Volet 2 : Redington, la promesse exacte et ses bords

Le théorème de Redington (1952) : valeur appariée, duration appariée, convexité d'actif
au moins égale, alors un PETIT déplacement PARALLÈLE ne peut pas réduire le surplus. Le
test `test_redington_wide_barbell_survives_parallel_shocks` le vérifie en forme fermée :
un barbell 2-30 ans satisfait les deux conditions et ne perd sous aucun choc parallèle de
± 100 pb. Mais le barbell 5-25 du banc, duration appariée, a MOINS de convexité que le
passif à queue de cinquante ans (testé : la condition du théorème est violée), et surtout
le théorème ne couvre ni les grands chocs ni les déformations : tout ce qui a compté
entre 2020 et 2023.

## Volet 3 : le banc de surplus (mesuré, `results/tables/surplus_mensuel.csv`)

Chaque fin de mois de 2019-12 à 2026-08 (81 courbes réelles), trois livres autofinancés
partent avec 5 % de surplus (précepte) et se rebalancent : « duration seule » (barbell de
zéro-coupon 5 et 25 ans appariant valeur et duration), « taux clés » (six zéro-coupon aux
nœuds 1-30 ans, chaque flux du passif réparti sur ses deux nœuds voisins en valeur
actualisée), « aucune » (tout à un an). Les rentes échues sont payées de l'actif ; aucun
apport extérieur.

![Surplus](results/figures/surplus.png)

**Comment lire cette figure.** Le surplus (actif moins passif) mois par mois. La courbe
jaune (taux clés) traverse la baisse de 2020 ET la hausse de 2022-23 (bande grise) sans
décrocher : elle passe de 81,3 à 92,5 M$ avec un creux à 77,3, c'est-à-dire qu'elle
s'accroît à peu près au taux sans risque, ce qu'un surplus immunisé doit faire. La bleue
(duration appariée par un seul barbell) erre sur une fourchette de 40,7 M$ : creux à 71,3
en avril 2020, sommet à 112,0 en janvier 2026, arrivée à 110,9. La déformation de la
courbe lui a été favorable CETTE FOIS ; l'errance est le prix de l'appariement grossier,
qui égale la duration mais pas la convexité. La verte (aucune couverture) plonge à -101,8 M$ en juillet 2020,
l'insolvabilité, puis finit à +329 M$ quand les taux montent : le même pari nu, gagné ou
perdu selon l'année.

Le creux résiduel du livre par taux clés (-9,5 M$ en septembre 2023, au plus fort de la
montée des taux longs ; le pic mensuel exact est octobre) vient du coin réglementaire :
TOUS les flux au-delà de 20 ans, actifs comme passif, s'actualisent sur le segment
interpolé vers l'UIR fixe à 4,5 %, mais pas avec la même sensibilité : le nœud d'actif à
30 ans y bouge à 0,8 fois le 20 ans de marché, pendant que les flux de passif de 40 à
50 ans, plus proches de l'UIR, bougent moins encore. L'appariement en valeur par nœuds ne
compense pas cette divergence de sensibilités du segment réglementaire ; l'écart se
referme quand la courbe se normalise (mesuré sur la trajectoire ; décomposition exacte
non isolée, déclaré).

## Volet 4 : l'exigence prescrite contre la perte réalisée

Au 2021-12, la veille du choc, l'exigence du module (livre duration, périmètre non
participant statique) vaut (mesuré, `results/tables/exigence_licat.csv`) :

| Scénario | Perte de valeur nette |
|---|---|
| **1 (tout baisse)** | **+7,4 M$ = l'exigence** |
| 2 (aplatissement) | -8,3 M$ (gain) |
| 3 (tout monte) | -10,1 M$ (gain) |
| 4 (pentification) | +5,6 M$ |
| Pire baisse de surplus réalisée sur les 18 mois suivants | **7,9 M$** |

![LICAT](results/figures/licat.png)

**Comment lire cette figure.** Les quatre barres sont les pertes prescrites ; deux mordent
un livre apparié en duration en DOLLARS, et la plus lourde, le scénario 1 (tout baisse),
fixe l'exigence à 7,4 M$. Un livre dont la duration en dollars est appariée ne perd rien
au premier ordre : ce qui reste est un effet de convexité, et le barbell 5-25 en a moins
que le passif, donc il perd des deux côtés. La ligne verte est la pire baisse de surplus
réellement subie sur les dix-huit mois suivants, rebalancements et rentes payées compris :
7,9 M$, une couverture de 93,5 %. Les deux grandeurs n'ont pas le même horizon, l'une
étant une revalorisation instantanée et l'autre un creux de trajectoire ; le ratio mesure
l'insuffisance du calibrage, pas une couverture au sens comptable (déclaré). Le double mécanisme est dans la formule : à un
90 jours sous 0,5 % fin 2021, les chocs en racine carrée étaient petits (le plus fort
choc court des quatre scénarios, +147 pb, quand la réalité en a livré +513) ; et le
mouvement réalisé, une hausse générale à dominante d'APLATISSEMENT, allait dans la
direction du scénario 2, que le module scorait en gain de 9,8 M$. L'exigence regardait
d'un côté, la perte est venue de l'autre. (Mesuré ; le livre par taux clés a subi
14,0 M$, couverture semblable.)

## Reproduire

```bash
uv sync --locked --all-extras
uv run pytest        # 14 tests fermés, sans réseau
uv run lic fetch     # courbe BdC (~17 Mo) + CPM2014 (ICA, 72 Ko)
uv run lic lab       # passif, trois bancs, exigence TSAV, trois figures (~1 min)
```

Les tests : structure initiale du TSAV (mi-chemin vers l'UIR à 45 ans, UIR à 70+),
duration d'un zéro-coupon en forme fermée t/(1+r), rente à mortalité constante contre la
série géométrique, chocs du chapitre 5 à la main (327 pb à 4 %), plancher de la racine à
0,5 %, UIR ± 40 pb, exigence nulle pour un livre parfaitement adossé, théorème de
Redington en forme fermée ET sa violation par le barbell serré, appariements exacts en
valeur et duration.

## Limites, avec statut

1. **Le périmètre est le module de taux, statique, non participant, au sans-risque pur.**
   Pas de lissage sur six trimestres (réservé aux blocs participants), pas de fonds
   distincts, pas d'agrégation avec les autres risques du TSAV, et l'écart d'actualisation
   prescrit par 5.1.1 lui-même (90 % de l'écart corporatif, ultime 80 pb) est omis : le
   chiffre de 7,4 M$ est le requis brut du scénario sur une valorisation sans risque, pas
   un ratio réglementaire. (Déclaré.)
2. **La valorisation suit la structure du TSAV partout**, y compris pour le surplus
   « économique » du banc : l'UIR fixe au-delà de 20-70 ans est une convention
   réglementaire, et le coin qu'il crée est discuté au volet 3. Une valorisation purement
   de marché au long bout donnerait des chemins voisins mais pas identiques. (Déclaré.)
3. **La mortalité est figée** (réalisée = attendue, table 2013 statique, hommes) : ni
   risque de longévité, ni amélioration au-delà de 2013 (ce qui sous-estime un peu la
   duration du passif). (Précepte déclaré.)
4. **Aucun frais, aucune prime, bloc fermé** : le banc isole la mécanique de taux.
   (Déclaré.)
5. **Le pire scénario dépend du livre.** La baisse générale mord NOTRE barbell, dont la
   convexité est inférieure à celle du passif ; un livre long en actif court aurait un
   autre pire scénario. Le constat de couverture (93,5 %) vaut pour ce bloc et cette
   période, pas en général. (Déclaré.)
6. **L'exigence et la perte réalisée n'ont pas le même horizon.** L'exigence est une
   revalorisation INSTANTANÉE au 2021-12-31 ; la perte réalisée est le creux d'une
   trajectoire de dix-huit mois, rebalancements et rentes payées compris. Le ratio des
   deux mesure l'insuffisance du calibrage, pas une couverture au sens comptable.
   (Déclaré.)
7. **Le banc apparie la duration en DOLLARS depuis l'audit du 2026-08-29.** La première
   version égalait les durations en ANNÉES sur un actif valant 1,05 fois le passif, ce qui
   laissait au surplus une exposition du PREMIER ordre au déplacement parallèle, exactement
   ce que le théorème de Redington sert à supprimer. Les chiffres publiés avant cette date
   (exigence 9,9 M$, perte réalisée 14,8 M$, couverture 67 %) portaient ce défaut.
   (Mesuré ; test `test_le_surplus_ne_baisse_pas_au_premier_ordre_sous_un_choc_parallele`.)

## Références

- OSFI, *Test de suffisance du capital des sociétés d'assurance vie (TSAV/LICAT) 2025*,
  chapitre 5, sections 5.1.1 à 5.1.2.3 (PDF officiel ; formules recopiées à la lettre).
- Redington, F. M. (1952), « Review of the principles of life-office valuations »,
  *Journal of the Institute of Actuaries* 78(3).
- Institut canadien des actuaires (2014), table CPM2014 et échelle CPM-B (classeur
  public, jamais commité).
- Bolder, D. J., G. Johnson et A. Metzler (2004), « An empirical analysis of the Canadian
  term structure of zero-coupon interest rates », Banque du Canada, WP 2004-48.

## English summary

A closed block of 10,000 male-65 life annuities (CIA CPM2014 mortality, 2013 static
column, declared) is backed by three self-financing books rebalanced monthly on real Bank
of Canada zero-coupon curves, Dec-2019 to Aug-2026: duration-matched barbell (5y/25y),
key-rate matched (six zero-coupon nodes), and no hedge (all 1-year). Measured: the
key-rate book ends where it started (81.3 to 80.6 M$) through a curve whose 10y-3m slope
went from +198 to -212 bp; the duration-only book wanders (75.7 to 104.3 M$, ending at
101.4: the happy ending is path luck,
and its convexity VIOLATES Redington's condition against a 50-year-tail liability,
tested); the unhedged book goes insolvent (-101.8 M$ in July 2020) before ending at
+329 M$. Redington's theorem itself is verified in closed form where it applies (wide
barbell, parallel shocks). The LICAT 2025 chapter-5 interest rate module is
re-implemented to the letter from OSFI's official PDF: shocks are linear in the SQUARE
ROOT of current rates (T+ at 4 % = +327 bp, hand-tested), four prescribed scenarios,
UIR 4.5 % shocked by 40 bp, worst-scenario requirement floored at zero. Verdict: computed
on Dec-2021 (90-day rate below 0.5 %, so the LARGEST prescribed short shock across the
four scenarios was only +147 bp while 2022-23 delivered +513, measured), the requirement
was 7.4 M$ (binding scenario: rates down) while the worst realized surplus drawdown over
the following eighteen months was 7.9 M$: 93.5 % coverage. What the duration-matched book
still loses is convexity, not duration: the 5-25 barbell is less convex than a liability
with a fifty-year tail, so the surplus falls on both sides of a parallel move. Risk-free-only
discounting: the 5.1.1 corporate-spread add-on is omitted and declared. Free data only,
15 closed-form tests.

## Licence et citation

Code sous licence MIT ; rapport et figures CC BY 4.0. Données : Banque du Canada
(attribution), ICA (classeur public cité, jamais redistribué), OSFI (ligne directrice
citée). Citer via `CITATION.cff`.
