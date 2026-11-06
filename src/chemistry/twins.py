"""Chemical twins: LOTUS compounds (via Wikidata) -> Jaccard similarity -> outputs/twins.csv.
Run: python -m src.chemistry.twins   (step 1 downloads data/lotus_compounds.csv, step 2 builds twins)
Optional data/iucn_status.csv (columns taxon,status) fills twin_iucn_status; otherwise 'not checked' (we did not look it up; that is not IUCN's own 'Not Evaluated').
"""
import os
import pandas as pd, requests
from src.chemistry.ema import ema_label, load_ema
from src.config import FAMILY, SPECIES

WDQS = "https://query.wikidata.org/sparql"
MIN_COMPOUNDS = 5  # Jaccard on tiny sets is noise


def fetch_family(family: str) -> pd.DataFrame:
    """All (taxon, InChIKey) pairs for taxa of a family: 'compound found in taxon' (P703)."""
    q = f'''SELECT ?taxon ?ik WHERE {{
      ?f wdt:P225 "{family}" . ?t wdt:P171+ ?f . ?t wdt:P225 ?taxon .
      ?c wdt:P703 ?t ; wdt:P235 ?ik . }}'''
    r = requests.get(WDQS, params={"query": q, "format": "json"}, timeout=300,
                     headers={"User-Agent": "vanishing-apothecary-hackathon/0.1"})
    r.raise_for_status()
    return pd.DataFrame([{"taxon": b["taxon"]["value"], "inchikey": b["ik"]["value"]}
                         for b in r.json()["results"]["bindings"]])


def is_species(name: str) -> bool:
    return len(name.replace("×", " ").split()) == 2  # drops genus-level items ("Salvia") and subspecies


def build_twins(comp: pd.DataFrame, species, family_of, status=None, top=5, ema=None) -> pd.DataFrame:
    # first 14 chars of an InChIKey = molecular skeleton, so stereoisomers count as the same compound
    comp = comp.assign(key=comp.inchikey.str[:14]).drop_duplicates(["taxon", "key"])
    sets = comp.groupby("taxon").key.agg(set)
    taxa_family = comp.drop_duplicates("taxon").set_index("taxon").get("family")
    rows = []
    for sp in species:
        if sp not in sets or len(sets[sp]) < MIN_COMPOUNDS:
            print(f"SKIP {sp}: {len(sets.get(sp, ()))} compounds in LOTUS"); continue
        cand = []
        for t, s in sets.items():
            if t == sp or not is_species(t) or len(s) < MIN_COMPOUNDS or taxa_family is None or taxa_family[t] != family_of[sp]:
                continue
            cand.append((t, len(s & sets[sp]) / len(s | sets[sp])))
        for t, sim in sorted(cand, key=lambda x: -x[1])[:top]:
            rows.append(dict(species=sp, twin=t, similarity=round(sim, 3),
                             twin_iucn_status=(status or {}).get(t, "not checked"), ema_evidence=ema_label(t, ema or {})))
    return pd.DataFrame(rows, columns=["species", "twin", "similarity", "twin_iucn_status", "ema_evidence"])


if __name__ == "__main__":
    if not os.path.exists("data/lotus_compounds.csv"):
        frames = [fetch_family(f).assign(family=f) for f in sorted(set(FAMILY.values()))]
        pd.concat(frames).to_csv("data/lotus_compounds.csv", index=False)
    comp = pd.read_csv("data/lotus_compounds.csv")
    st = pd.read_csv("data/iucn_status.csv").set_index("taxon").status.to_dict() if os.path.exists("data/iucn_status.csv") else None
    out = build_twins(comp, SPECIES, FAMILY, st, ema=load_ema())
    os.makedirs("outputs", exist_ok=True)
    out.to_csv("outputs/twins.csv", index=False)
    print(out)
