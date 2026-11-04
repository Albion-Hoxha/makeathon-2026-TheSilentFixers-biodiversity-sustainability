"""Shared settings: every module imports species and region from here."""
SPECIES = [
    "Salvia officinalis",
    "Gentiana lutea",
    "Arnica montana",
    "Origanum vulgare",
    "Hypericum perforatum",
]
# Western Balkans bounding box (lon_min, lat_min, lon_max, lat_max)
BBOX = (13.0, 39.5, 23.5, 46.5)
# Family used to pick candidate "chemical twins" from LOTUS/Wikidata
FAMILY = {
    "Salvia officinalis": "Lamiaceae",
    "Gentiana lutea": "Gentianaceae",
    "Arnica montana": "Asteraceae",
    "Origanum vulgare": "Lamiaceae",
    "Hypericum perforatum": "Hypericaceae",
}
# Checked live on GBIF/Wikidata, 2026-11-04: too little data to model, reported as a data-gap finding (see README)
DATA_GAP = {"Sideritis scardica": {"gbif_records_in_region": 43, "usable_after_filters": 23, "lotus_compounds": 2}}
