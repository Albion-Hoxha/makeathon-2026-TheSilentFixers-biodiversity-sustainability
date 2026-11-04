import pandas as pd
from src.chemistry.twins import build_twins


def test_closest_same_family_twin_wins():
    rows = [("A a", f"{i:014d}XX", "Fam") for i in range(10)]                       # species A: 10 compounds
    rows += [("B b", f"{i:014d}YY", "Fam") for i in range(8)] + [("B b", "Z" * 14 + "AA", "Fam")]   # B shares 8 (stereo suffix differs)
    rows += [("C c", f"{i:014d}XX", "Other") for i in range(10)]                    # same chemistry, wrong family -> excluded
    rows += [("D d", f"{i:014d}XX", "Fam") for i in range(2)]                       # too few compounds -> excluded
    df = pd.DataFrame(rows, columns=["taxon", "inchikey", "family"])
    out = build_twins(df, ["A a"], {"A a": "Fam"})
    assert list(out.twin) == ["B b"] and out.similarity[0] == round(8 / 11, 3)


def test_status_default_is_not_read_back_as_missing(tmp_path):
    rows = [("A a", f"{i:014d}XX", "F") for i in range(6)] + [("B b", f"{i:014d}XX", "F") for i in range(6)]
    out = build_twins(pd.DataFrame(rows, columns=["taxon", "inchikey", "family"]), ["A a"], {"A a": "F"})
    out.to_csv(tmp_path / "t.csv", index=False)
    assert pd.read_csv(tmp_path / "t.csv").twin_iucn_status.notna().all()  # "NA" would come back as NaN -> shown as None


def test_genus_level_items_are_not_twins_and_ema_label_is_attached():
    from src.chemistry.ema import ema_label, load_ema
    rows = [(t, f"{i:014d}XX", "F") for t in ["A b", "Salvia", "Salvia tomentosa", "Mentha × piperita"] for i in range(6)]
    out = build_twins(pd.DataFrame(rows, columns=["taxon", "inchikey", "family"]), ["A b"], {"A b": "F"},
                      ema={"mentha piperita": "both"})
    assert "Salvia" not in set(out.twin)
    assert dict(zip(out.twin, out.ema_evidence))["Mentha × piperita"] == "well-established + traditional use"
    assert dict(zip(out.twin, out.ema_evidence))["Salvia tomentosa"] == "no EU monograph"
    tab = load_ema()  # the committed table: focal species + one that is not covered
    assert ema_label("Gentiana lutea", tab) == "traditional use" and ema_label("Origanum vulgare", tab) == "no EU monograph"
    assert ema_label("Hypericum perforatum", tab) == "well-established + traditional use"
