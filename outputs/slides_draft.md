# Vanishing Apothecary — slide draft

**Track 3: Biodiversity & Sustainability · linked to Track 2: Natural Products**  
Draft of 9 slides. Climate figures below come from the committed model outputs; Chemical Twin values come from `outputs/twins.csv` and `data/lotus_compounds.csv`.

---

## Slide 1 — Balkan medicinal plants under pressure

- Wild medicinal plants support local traditions and commercial supply chains.
- Some species face harvesting pressure while climate change shifts suitable conditions toward cooler, higher elevations.
- Regional planners lack a single view of future climate suitability and possible chemical relatives.
- **Project question:** Where could suitable habitat change by 2041–2060, and which same-family plants share reported natural products?

**Visual:** Western Balkans map with five focal plant names and two question callouts: “Where may suitability change?” and “Which relatives merit further study?”

---

## Slide 2 — Study species and data

**Five modelled species**

| Species | Family | GBIF records used |
|---|---|---:|
| *Salvia officinalis* | Lamiaceae | 1,551 |
| *Gentiana lutea* | Gentianaceae | 802 |
| *Arnica montana* | Asteraceae | 167 |
| *Origanum vulgare* | Lamiaceae | 917 |
| *Hypericum perforatum* | Hypericaceae | 1,408 |

- **Climate:** WorldClim 2.1 bioclimatic variables and CMIP6 projections for 2041–2060.
- **Natural products:** LOTUS-linked Wikidata records, using “found in taxon” (P703) and InChIKey (P235).
- **EMA:** EU herbal monograph evidence for candidate species.
- **GBIF:** coordinate records filtered for uncertainty under 5 km and duplicate coordinates.

*Data-gap note:* *Sideritis scardica* was excluded: the project records 23 usable regional GBIF locations and 2 LOTUS compounds, below the model’s minimums.

**Source note:** Project files `data/occurrences.csv`, `data/lotus_compounds.csv`, `data/ema_monographs.csv`; README records source licences.

---

## Slide 3 — Methods: climate suitability and chemical overlap

**Climate model**

1. Thin occurrences to one presence per 2.5-arc-minute climate cell.
2. Fit a Random Forest presence/background model with 5,000 background cells.
3. Set the suitability threshold at the 10th percentile of held-out presences.
4. Evaluate with 1-degree spatial-block cross-validation.
5. Project to six scenario/GCM combinations: SSP2-4.5 and SSP5-8.5, each with three GCMs.

**Chemical Twins**

- Compare plants only within the focal plant’s family.
- Count distinct InChIKey skeletons (first 14 characters); require at least five compounds per plant.
- Rank species-level candidates by Jaccard similarity and attach EMA evidence.

**Visual:** Two compact pipelines: GBIF → climate model → 2050 suitability; LOTUS → compound sets → Jaccard-ranked relatives.

---

## Slide 4 — Climate results: modelled suitable area

**Projected change in suitable area, 2041–2060 mean across six scenario/GCM runs**

| Species | Spatial-CV AUC | Modelled area change |
|---|---:|---:|
| *Salvia officinalis* | 0.776 | **+86.2%** |
| *Gentiana lutea* | 0.905 | **−7.1%** |
| *Arnica montana* | 0.798 | **+53.2%** |
| *Origanum vulgare* | 0.729 | **+59.6%** |
| *Hypericum perforatum* | 0.714 | **+71.7%** |

- Four species have a larger modelled suitable area in the future mean; *Gentiana lutea* is the only one with a smaller mean area.
- For *Gentiana lutea*, individual scenario/GCM runs range from **4.0% area gain to 23.8% area loss**.
- Mean spatial-CV AUC across the five models: **0.784**.

**Read the sign correctly:** `outputs/risk.csv` stores `loss_pct`; negative values mean modelled area gain. The table above presents area change, so positive means gain and negative means loss.

**Visual:** Horizontal bars centred at zero, with gains to the right and losses to the left; show Gentiana’s scenario range separately.

**Source:** `outputs/risk.csv`, `outputs/risk_scenarios.csv`. Area change is modelled suitability area, not observed population growth or decline.

---

## Slide 5 — Chemical Twins and EMA evidence

**Top-ranked same-family candidate for each focal plant**

| Focal species | Top candidate | Jaccard | EMA evidence |
|---|---|---:|---|
| *Salvia officinalis* | *Rosmarinus officinalis* | 0.290 | Traditional use |
| *Gentiana lutea* | *Gentianella campestris* | 0.275 | No EU monograph |
| *Arnica montana* | *Arnica chamissonis* | 0.114 | No EU monograph |
| *Origanum vulgare* | *Thymus longicaulis* | 0.281 | No EU monograph |
| *Hypericum perforatum* | *Hypericum maculatum* | 0.221 | No EU monograph |

- LOTUS records **319, 97, 122, 160 and 207** distinct compound skeletons for the five focal species, respectively.
- *Gentiana lutea* has the lowest LOTUS coverage (97), followed by *Arnica montana* (122); both exceed the five-compound minimum.
- Across all 25 ranked pairs: **4** have EMA “traditional use” evidence; **21** have “no EU monograph.” All 25 candidate IUCN statuses are “not assessed.”

**Caution:** Jaccard measures overlap in database records. Chemical overlap does not establish equal medicinal effect, safety or substitutability. Twins are research candidates only.

**Source:** `outputs/twins.csv`, `data/lotus_compounds.csv`, `data/ema_monographs.csv`.

---

## Slide 6 — Interactive dashboard

- Seven views: Overview, Species Explorer, Climate Explorer, Chemical Twins, Risk Analytics, Conservation, and Data & Methods.
- Select a species to view GBIF occurrence points, current and 2050 model maps, risk metrics and ranked chemical relatives.
- The Chemical Twins view shows the Jaccard network, similarity ranking, EMA evidence and shared compound counts.
- Risk categories use project-defined cutoffs: Low <10%, Medium <30%, High ≥30%; these are not IUCN categories.

**Visual:** Dashboard screenshot with one selected species, its model map and twin ranking.

**Source:** `app/app.py`, `app/theme.py`, `outputs/maps/`, and the CSV outputs.

---

## Slide 7 — Limitations and uncertainty

- GBIF sampling is uneven; coordinate filtering and spatial validation reduce bias but do not remove it.
- Climate models disagree, especially for *Gentiana lutea*; report the scenario/GCM range.
- Suitable area is not abundance, population trend, extinction probability or harvest pressure.
- LOTUS coverage varies by species; lower coverage can make rankings less complete. The source GeoTIFFs are not stored in Git, so exact model reproduction requires the matching local climate stacks.
- IUCN statuses are not assessed in the current twin file. WDPA protected-area overlap is listed as future work, not an integrated result.
- EMA traditional-use evidence is regulatory context, not proof that a candidate is a safe or effective substitute.

---

## Slide 8 — Conservation impact and next steps

- Field-check modelled suitable areas with local botanists, especially *Gentiana lutea*, whose mean projection shows a 7.1% decrease and whose scenario runs disagree.
- Add harvest-pressure data before making sourcing recommendations.
- Overlay future suitability with WDPA protected areas and identify sites needing monitoring.
- Evaluate cultivation and chemistry of same-family candidates in the lab; do not recommend medicinal substitution from Jaccard scores alone.
- Archive climate inputs, model versions and GCM metadata so the results can be reproduced.

**Intended use:** Help conservation planners identify locations and species for follow-up; help cooperatives frame sustainable-sourcing research.

---

## Slide 9 — Team and AI disclosure

- **Albion Hoxha — Team Lead & Integration:** coordination, integration, deployment and submission.
- **Afron Makolli — Climate & Spatial Modelling:** GBIF pipeline, species-distribution modelling and 2050 maps.
- **Rinesa Sekiraca — Chemistry & Dashboard:** LOTUS pipeline, Chemical Twins, dashboard and slides.
- **AI disclosure:** Claude assisted with research, code scaffolding and documentation drafts; GitHub Copilot assisted with code completion. The team made and reviewed the scientific choices and results.

---

## Presenter checks before submission

- Confirm the dashboard is loading `outputs/risk.csv` and `outputs/twins.csv`, not `sample_*.csv`.
- Keep negative `loss_pct` values labelled as **area gains** when presenting.
- Cite dataset versions and licences on the Data slide; add final figure/source credits to slide notes.
- Do not describe Chemical Twins as medical substitutes.
