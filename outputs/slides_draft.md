# Vanishing Apothecary — slide draft

**Track 3: Biodiversity & Sustainability · linked to Track 2: Natural Products**  
Draft of 9 slides. Climate results below use the current guarded model outputs; Chemical Twins values come from `outputs/twins.csv` and `data/lotus_compounds.csv`.

---

## Slide 1 — Balkan medicinal plants under pressure

- Wild medicinal plants support local traditions and commercial supply chains.
- Some species face harvesting pressure while climate change can shift suitable conditions toward cooler, higher elevations.
- Conservation planners need to see where modelled habitat may change and which chemical relatives merit further research.
- **Project question:** Where could suitable habitat change by 2041–2060, and which same-family plants share reported natural products?

**Visual:** Sharr mountain hero photograph with the project title and question.

**Photo credit:** “Small Turk and Titov Vrv” by Vojkan Nedkovski, CC BY-SA 4.0, via Wikimedia Commons. Include this credit on the slide itself.

---

## Slide 2 — Study species and data

**Five modelled species**

| Species | Family | GBIF records used |
|---|---|---:|
| *Salvia officinalis* | Lamiaceae | 1,531 |
| *Gentiana lutea* | Gentianaceae | 780 |
| *Arnica montana* | Asteraceae | 163 |
| *Origanum vulgare* | Lamiaceae | 860 |
| *Hypericum perforatum* | Hypericaceae | 1,382 |

- **Occurrences:** GBIF records after coordinate and quality filtering.
- **Climate:** WorldClim 2.1 bioclimatic variables and CMIP6 projections for 2041–2060.
- **Natural products:** LOTUS-linked Wikidata records: “found in taxon” (P703) and InChIKey (P235).
- **Regulatory context:** EMA herbal monograph evidence for candidate plants.

*Data-gap note:* *Sideritis scardica* was excluded: 23 usable regional GBIF locations and 2 LOTUS compounds, below the project’s model and chemical-comparison minimums.

**Sources:** `data/occurrences.csv`, `data/lotus_compounds.csv`, `data/ema_monographs.csv`, and the climate rasters used for the committed model outputs.

---

## Slide 3 — Methods: chemical overlap

- Compare plants within the focal species’ family.
- Compare distinct InChIKey skeletons (first 14 characters), requiring at least five per species.
- Rank species-level candidates by **Jaccard similarity** and attach EMA evidence.

**Visual:** LOTUS → compound sets → Jaccard-ranked relatives. Chemical similarity identifies research candidates, not medical substitutes.

---

## Slide 4 — Climate model and validation

- Thin occurrences to one presence per 2.5-arc-minute climate cell and fit a Random Forest presence/background model with 5,000 background cells.
- Choose the suitability threshold that maximises **TSS** on held-out spatial blocks.
- Evaluate with 1-degree spatial-block cross-validation and project to six CMIP6 scenario/GCM combinations: SSP2-4.5 and SSP5-8.5, each with three GCMs.
- Apply a **climate-envelope guard**: count future cells as suitable only when their bioclimatic values remain within the ranges observed at presence locations.
- Spatial cross-validation AUC by species: *Salvia officinalis* 0.787; *Gentiana lutea* 0.912; *Arnica montana* 0.918; *Origanum vulgare* 0.726; *Hypericum perforatum* 0.723.
- Mean spatial-CV AUC: **0.813**.
- Scores describe discrimination on held-out spatial blocks; they do not establish population trends or extinction probability.

**Source:** `outputs/risk.csv`. Values rounded to three decimals.

---

## Slide 5 — Climate results: guarded habitat change

**Mean projected suitable-area change, 2041–2060, across six scenario/GCM runs**

| Species | Guarded area change | Unguarded area change |
|---|---:|---:|
| *Salvia officinalis* | **−21.5%** | +58.0% |
| *Gentiana lutea* | **−81.3%** | −80.0% |
| *Arnica montana* | **−71.0%** | −38.1% |
| *Origanum vulgare* | **−28.5%** | +0.6% |
| *Hypericum perforatum* | **−15.9%** | +49.4% |

*Positive values are gains; negative values are losses in this table.* The guarded mean projected loss across five species is **43.6%**. For *Gentiana lutea*, guarded scenario/GCM results range from 70.7% to 91.0% loss.

**Interpretation:** Three species change direction between guarded and unguarded estimates. Any unguarded gains are **model-dependent** and may reflect Random Forest extrapolation beyond the observed climate envelope.

**Conservative-loss note:** The guard counts habitat outside the observed climate envelope as unsuitable. This makes the estimated losses a conservative, pessimistic estimate of future suitable area; it does not mean observed populations will decline by the same percentage.

**Source:** `outputs/risk.csv`, `outputs/risk_scenarios.csv`. These are modelled suitability-area changes, not population forecasts.

---

## Slide 6 — Chemical Twins and EMA evidence

**Top-ranked same-family candidate for each focal plant**

| Focal species | Top candidate | Jaccard | EMA evidence |
|---|---|---:|---|
| *Salvia officinalis* | *Rosmarinus officinalis* (*Salvia rosmarinus*) | 0.290 | Traditional use |
| *Gentiana lutea* | *Gentianella campestris* | 0.275 | No EU monograph |
| *Arnica montana* | *Arnica chamissonis* | 0.114 | No EU monograph |
| *Origanum vulgare* | *Thymus longicaulis* | 0.281 | No EU monograph |
| *Hypericum perforatum* | *Hypericum maculatum* | 0.221 | No EU monograph |

- LOTUS has **319, 97, 122, 160 and 207** distinct compound skeletons for the five focal species, respectively.
- *Gentiana lutea* has the lowest LOTUS coverage (97), followed by *Arnica montana* (122); both exceed the five-compound minimum.
- Across 25 pairs, **4** are labelled EMA “traditional use” and **21** “no EU monograph.” The label describes monograph evidence, not therapeutic equivalence.
- EMA lists the sage monograph under *Rosmarinus officinalis*; the accepted botanical name is *Salvia rosmarinus*.
Candidate IUCN labels: 24 Not Evaluated, 1 sources disagree (Origanum dictamnus: Least Concern in GBIF, Near Threatened in Wikidata); regional/national assessments are not included.

**Caution:** Jaccard measures overlap in database records. Chemical overlap does not establish equal medicinal effect, safety or substitutability. Twins are research candidates only.

**Sources:** `outputs/twins.csv`, `data/lotus_compounds.csv`, `data/ema_monographs.csv`, `data/iucn_status.csv`.

---

## Slide 7 — Interactive dashboard

- Seven views: Overview, Species Explorer, Climate Explorer, Chemical Twins, Risk Analytics, Conservation, and Data & Methods.
- Select a species to inspect occurrence records, current and 2050 model maps, risk metrics and ranked chemical relatives.
- Chemical Twins displays the Jaccard network and rankings, shared chemical skeletons, EMA evidence and IUCN labels from the bundled checklist data.
- Risk categories use project-defined cutoffs; they are not IUCN categories.

**Visual:** Use the real screenshot `docs/screenshots/04_climate_explorer_gentiana.jpg` or `docs/screenshots/05_chemical_twins.jpg`; keep the selected species and chart/map readable.

**Source:** `app/app.py`, `docs/screenshots/`, `outputs/` and `data/`.

---

## Slide 8 — Limitations, conservation and next steps

- GBIF sampling is uneven; coordinate filtering and spatial validation reduce bias but do not remove it.
- Climate projections differ across GCMs. The guarded model treats future habitat outside the observed climate envelope as unsuitable, so the loss estimates are conservative/pessimistic; compare guarded and unguarded values and label gains **model-dependent**.
- Suitable area is not abundance, population trend, extinction probability or harvest pressure.
- WDPA protected-area overlap and harvest-pressure data are not integrated results; they remain next steps.
- Field-check priority areas with local botanists, especially *Gentiana lutea*, and evaluate cultivation and candidate chemistry in research settings.
- Do not recommend medicinal substitution from chemical similarity alone.
- **Intended use:** Help conservation planners identify places and species for follow-up, and frame sustainable-sourcing research with local cooperatives.

**Conservative-loss note:** Because cells outside the observed climate envelope count as unsuitable, estimated losses may be higher than estimates without that filter. The new model outputs provide the guarded and unguarded comparison; neither is direct evidence of population change.

---

## Slide 9 — Team and AI disclosure

- **Albion Hoxha — Team Lead & Integration:** coordination, integration, deployment and submission.
- **Afron Makolli — Climate & Spatial Modelling:** GBIF pipeline, species-distribution modelling and 2050 projections.
- **Rinesa Sekiraça — Chemistry & Dashboard:** LOTUS pipeline, Chemical Twins, dashboard and slides.
- **AI disclosure:** Claude supported research, code scaffolding and documentation drafts; Codex assisted with coding and review. The team made and reviewed the scientific choices and results.

**Presenter checks:** confirm screenshots show the latest dashboard outputs; keep units, signs and guard labels visible; cite data sources and photo credits on the slides.
