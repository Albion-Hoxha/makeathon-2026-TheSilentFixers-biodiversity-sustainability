"""Download GBIF occurrences for SPECIES -> data/occurrences.csv. Run: python -m src.climate.fetch_gbif"""
import pandas as pd, requests
from src.config import SPECIES, BBOX

API = "https://api.gbif.org/v1/occurrence/search"

def fetch(species: str, max_records: int = 3000) -> list[dict]:
    lon0, lat0, lon1, lat1 = BBOX
    rows, offset = [], 0
    while offset < max_records:
        r = requests.get(API, timeout=60, params={
            "scientificName": species, "hasCoordinate": "true", "hasGeospatialIssue": "false",
            "decimalLongitude": f"{lon0},{lon1}", "decimalLatitude": f"{lat0},{lat1}",
            "year": "1970,2026", "occurrenceStatus": "PRESENT",  # WorldClim baseline is 1970-2000
            "limit": 300, "offset": offset})
        r.raise_for_status()
        d = r.json()
        rows += [{"species": species, "lon": o["decimalLongitude"], "lat": o["decimalLatitude"],
                  "uncertainty_m": o.get("coordinateUncertaintyInMeters"), "year": o.get("year"), "basis": o.get("basisOfRecord")}
                 for o in d["results"]]
        if d["endOfRecords"]:
            break
        offset += 300
    return rows

if __name__ == "__main__":
    df = pd.DataFrame([x for s in SPECIES for x in fetch(s)])
    df = df[df.uncertainty_m.isna() | (df.uncertainty_m < 5000)]
    df = df[df.basis != "LIVING_SPECIMEN"]  # limit: planted garden records seen as human observations cannot be separated (GBIF establishmentMeans is empty)
    df = df.drop_duplicates(["species", "lon", "lat"])  # shortcut: no spatial thinning yet, add in the SDM step
    df.to_csv("data/occurrences.csv", index=False)
    print(df.groupby("species").size())  # <30 records for a species -> tell the team lead
