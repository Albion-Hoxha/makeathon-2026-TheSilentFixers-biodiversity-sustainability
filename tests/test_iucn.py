import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import fetch_iucn


class R:
    def __init__(self, data, ok=True): self._d, self.ok = data, ok
    def json(self): return self._d


def test_synonym_is_resolved_to_the_accepted_name_and_its_category(monkeypatch):
    def fake_get(path, **p):
        if path == "species/match": return R({"usageKey": 1})
        if path == "species/1": return R({"acceptedKey": 2, "scientificName": "Old name L."})
        if path == "species/2": return R({"canonicalName": "New name"})
        if path == "species/2/iucnRedListCategory": return R({"category": "LEAST_CONCERN"})
        raise AssertionError(path)
    monkeypatch.setattr(fetch_iucn, "get", fake_get)
    assert fetch_iucn.lookup("Old name") == dict(taxon="Old name", status="Least Concern", accepted_name="New name", gbif_key=2)


def test_missing_category_is_reported_not_invented(monkeypatch):
    monkeypatch.setattr(fetch_iucn, "get", lambda path, **p: R({"usageKey": 5}) if path == "species/match" else
                        R({}) if path == "species/5" else R({}, ok=False))
    r = fetch_iucn.lookup("X y")
    assert r["status"] == "not in GBIF IUCN checklist"


def test_reconcile_never_guesses_when_sources_conflict():
    r = fetch_iucn.reconcile
    assert r("Least Concern", None) == "Least Concern"           # Wikidata has nothing: keep GBIF
    assert r("Least Concern", "least concern") == "Least Concern"  # agree
    assert r("Least Concern", "Near Threatened") == "sources disagree"
    assert r("Not Evaluated", "Vulnerable") == "sources disagree"  # one source stale
