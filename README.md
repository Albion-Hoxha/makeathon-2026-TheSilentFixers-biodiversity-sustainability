# Vanishing Apothecary: Climate Risk & Chemical Twins
EthnoHack 2026 · Track 3 (Biodiversity & Sustainability), linked to Track 2 (Natural Products)

Where will Balkan medicinal plants lose their habitat by 2050, and which chemically similar plants could take the harvesting pressure off them?

## Quick start
```bash
pip install -r requirements.txt
python -m src.climate.fetch_gbif     # -> data/occurrences.csv
python -m src.climate.sdm            # needs data/climate/current.tif + future_*.tif -> outputs/risk.csv + maps
python -m src.chemistry.twins        # -> data/lotus_compounds.csv, outputs/twins.csv
python -m pytest -q                  # tests on synthetic data
streamlit run app/app.py             # dashboard (shows SAMPLE DATA banner until outputs/risk.csv exists)
```

## Who does what (hand-off files must keep these exact columns)
| Owner | Work | Output |
|---|---|---|
| Afron (climate) | GBIF + WorldClim -> MaxEnt (`elapid`), now vs 2050 (SSP2-4.5, SSP5-8.5), spatial CV | `outputs/risk.csv`: `species,n_records,area_now_km2,area_2050_km2,loss_pct,auc` and maps `outputs/maps/<species>_now.png`, `<species>_2050.png` |
| Rinesa (chemistry + app) | LOTUS via Wikidata SPARQL (P703), Jaccard/Tanimoto similarity, dashboard, slides | `outputs/twins.csv`: `species,twin,similarity,twin_iucn_status` |
| Albion (lead) | integration, deploy, Devpost, video | |

Species and region live in `src/config.py`. Put climate code in `src/climate/`, chemistry in `src/chemistry/`.

## Climate rasters (not in git)
Download WorldClim 2.1 bioclim (2.5 arcmin) for the current climate, and CMIP6 2041-2060 (SSP2-4.5 and SSP5-8.5, 2-3 GCMs). Each file must be ONE multi-band GeoTIFF with the 19 bio variables in the same band order. Save as `data/climate/current.tif` and `data/climate/future_<scenario>_<gcm>.tif` (the WorldClim future files are already multi-band; for the current climate stack the 19 `bio_*.tif` files, e.g. `gdal_merge.py -separate`).

## Method notes
Random Forest presence/background model (not MaxEnt: fewer dependencies, same idea), one presence per 2.5' cell, 5000 background cells, 1-degree spatial block CV for AUC, suitability threshold = 10th percentile of held-out presences. Twins: Jaccard similarity on InChIKey skeletons (first 14 chars) between species of the same family, at least 5 compounds each.

## Species and a data-gap finding
Modelled species: *Salvia officinalis, Gentiana lutea, Arnica montana, Origanum vulgare, Hypericum perforatum*.
*Sideritis scardica* (Greek/Balkan mountain tea) was planned but cannot be modelled: on 2026-11-04 GBIF had 43 records in our region (23 usable after quality filters, below our minimum of 30) and LOTUS/Wikidata only 2 compounds (minimum 5). We report this as a data gap rather than force a model on too little data.

## Dashboard (app/)
`streamlit run app/app.py`: 7 pages (Overview, Species Explorer, Climate Explorer, Chemical Twins, Risk Analytics, Conservation, Data & Methods). Every number is read from `outputs/risk.csv`, `risk_scenarios.csv` and `twins.csv`; without them it shows `outputs/sample_*.csv` under a SAMPLE DATA banner. Optional images: `app/assets/hero.jpg` and `app/assets/species/<Species name>.jpg` (use only photos with a licence that allows it and credit them in the README).

## Data and licences
GBIF (CC0/CC-BY), WorldClim 2.1 (CC-BY 4.0), LOTUS (CC0), IUCN Red List and WDPA (non-commercial terms, cite).

## Limits
Chemical similarity does not imply equal therapeutic effect: twins are research candidates, not medical substitutes. Sample files in `outputs/sample_*.csv` are placeholders, not results.

## AI usage
Claude (Anthropic) and GitHub Copilot assisted with code scaffolding and documentation. The team reviews all results.
