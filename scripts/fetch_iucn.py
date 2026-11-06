"""IUCN Red List category + accepted name for our plants and twin candidates -> data/iucn_status.csv.
Sources: GBIF's copy of the IUCN Red List checklist and Wikidata (P141), both secondary copies of the IUCN global assessment (no API key).
Where they disagree the category is reported as "sources disagree" instead of guessing; verify those at iucnredlist.org.
Regional and national assessments (European Red List, national red lists) are NOT included and can differ from the global category.
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


def wikidata_status(names):
    """{taxon: IUCN status label} from Wikidata P141 for taxa that have one."""
    vals = " ".join(f'"{n}"' for n in names)
    q = f'''SELECT ?name ?sl WHERE {{ VALUES ?name {{ {vals} }} ?t wdt:P225 ?name ; wdt:P141 ?s .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". ?s rdfs:label ?sl }} }}'''
    r = requests.get("https://query.wikidata.org/sparql", params={"query": q, "format": "json"}, headers=H, timeout=120)
    r.raise_for_status()
    return {b["name"]["value"]: b["sl"]["value"].title() for b in r.json()["results"]["bindings"]}


def reconcile(gbif: str, wiki: str | None) -> str:
    """Agreed category, the GBIF one when Wikidata has none, or 'sources disagree'."""
    if not wiki or wiki.lower() == gbif.lower():
        return gbif
    return "sources disagree"


if __name__ == "__main__":
    from src.config import SPECIES
    tw = pd.read_csv(ROOT / "outputs" / "twins.csv")
    taxa = sorted(set(SPECIES) | set(tw.species) | set(tw.twin))
    out = pd.DataFrame([lookup(t) for t in taxa]).rename(columns={"status": "status_gbif"})
    wd = wikidata_status(taxa)
    out["status_wikidata"] = out.taxon.map(wd).fillna("")
    out.insert(1, "status", [reconcile(g, w) for g, w in zip(out.status_gbif, out.status_wikidata)])
    out["source"] = "GBIF copy of the IUCN checklist + Wikidata P141 (global assessments only)"
    out["retrieved"] = datetime.date.today().isoformat()
    out.to_csv(ROOT / "data" / "iucn_status.csv", index=False)
    print(out[["taxon", "status", "status_gbif", "status_wikidata", "accepted_name"]].to_string(index=False))
