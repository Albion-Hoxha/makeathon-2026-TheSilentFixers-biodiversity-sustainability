"""Shared settings: every module imports species and region from here."""
SPECIES = [
    "Sideritis scardica",
    "Gentiana lutea",
    "Arnica montana",
    "Origanum vulgare",
    "Hypericum perforatum",
]
# Western Balkans bounding box (lon_min, lat_min, lon_max, lat_max)
BBOX = (13.0, 39.5, 23.5, 46.5)
# Family used to pick candidate "chemical twins" from LOTUS/Wikidata
FAMILY = {
    "Sideritis scardica": "Lamiaceae",
    "Gentiana lutea": "Gentianaceae",
    "Arnica montana": "Asteraceae",
    "Origanum vulgare": "Lamiaceae",
    "Hypericum perforatum": "Hypericaceae",
}
