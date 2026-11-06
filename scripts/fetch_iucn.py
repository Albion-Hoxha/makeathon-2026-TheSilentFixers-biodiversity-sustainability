"""IUCN Red List category + accepted name for our plants and twin candidates -> data/iucn_status.csv.
Source: GBIF's copy of the IUCN Red List checklist (no API key). It can lag behind iucnredlist.org, so verify key species there.
Run after the twins exist: python scripts/fetch_iucn.py     (twins.py then reads the file)"""
import datetime, sys
from pathlib import Path
import pandas as pd, requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # so `from src.config` works when run as a script
H = {"User-Agent": "vanishing-apothecary-hackathon/0.1"}
CAT = {"LEAST_CONCERN": "Least Concern", "NEAR_THREATENED": "Near Threatened", "VULNERABLE": "Vulnerable", "ENDANGERED": "Endangered",
       "CRITICALLY_ENDANGERED": "Critically Endangered", "EXTINCT_IN_THE_WILD": "Extinct in the Wild", "EXTINCT": "Extinct",
       "DATA_DEFICIENT": "Data Deficient", "NOT_EVALUATED": "Not Evaluated"}


def get(path, **params):
    return requests.get("https://api.gbif.org/v1/" + path, params=params, headers=H, timeout=30)


def lookup(name: str) -> dict:
    m = get("species/match", name=name).json()
    key = m.get("usageKey")
    if not key:
        return dict(taxon=name, status="not found in GBIF", accepted_name="", gbif_key="")
    info = get(f"species/{key}").json()
    acc_key = info.get("acceptedKey", key)  # synonyms point to their accepted name
    acc = info if acc_key == key else get(f"species/{acc_key}").json()
    r = get(f"species/{acc_key}/iucnRedListCategory")
    cat = CAT.get(r.json().get("category"), r.json().get("category")) if r.ok else "not in GBIF IUCN checklist"
    return dict(taxon=name, status=cat, accepted_name=acc.get("canonicalName") or acc.get("scientificName", ""), gbif_key=acc_key)


if __name__ == "__main__":
    from src.config import SPECIES
    tw = pd.read_csv(ROOT / "outputs" / "twins.csv")
    taxa = sorted(set(SPECIES) | set(tw.species) | set(tw.twin))
    out = pd.DataFrame([lookup(t) for t in taxa])
    out["source"] = "GBIF copy of the IUCN Red List checklist"
    out["retrieved"] = datetime.date.today().isoformat()
    out.to_csv(ROOT / "data" / "iucn_status.csv", index=False)
    print(out[["taxon", "status", "accepted_name"]].to_string(index=False))
