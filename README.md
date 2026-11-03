# Vanishing Apothecary: Climate Risk & Chemical Twins
EthnoHack 2026 · Track 3 (Biodiversity & Sustainability), linked to Track 2 (Natural Products)

Where will Balkan medicinal plants lose their habitat by 2050, and which chemically similar plants could take the harvesting pressure off them?

## Quick start
```bash
pip install -r requirements.txt
python -m src.climate.fetch_gbif     # -> data/occurrences.csv
streamlit run app/app.py             # dashboard (shows SAMPLE DATA banner until outputs/risk.csv exists)
```

## Who does what (hand-off files must keep these exact columns)
| Owner | Work | Output |
|---|---|---|
| Afron (climate) | GBIF + WorldClim -> MaxEnt (`elapid`), now vs 2050 (SSP2-4.5, SSP5-8.5), spatial CV | `outputs/risk.csv`: `species,n_records,area_now_km2,area_2050_km2,loss_pct,auc` and maps `outputs/maps/<species>_now.png`, `<species>_2050.png` |
| Rinesa (chemistry + app) | LOTUS via Wikidata SPARQL (P703), Jaccard/Tanimoto similarity, dashboard, slides | `outputs/twins.csv`: `species,twin,similarity,twin_iucn_status` |
| Albion (lead) | integration, deploy, Devpost, video | |

Species and region live in `src/config.py`. Put climate code in `src/climate/`, chemistry in `src/chemistry/`.

## Data and licences
GBIF (CC0/CC-BY), WorldClim 2.1 (CC-BY 4.0), LOTUS (CC0), IUCN Red List and WDPA (non-commercial terms, cite).

## Limits
Chemical similarity does not imply equal therapeutic effect: twins are research candidates, not medical substitutes. Sample files in `outputs/sample_*.csv` are placeholders, not results.

## AI usage
Claude (Anthropic) and GitHub Copilot assisted with code scaffolding and documentation. The team reviews all results.
