import pandas as pd
from src.chemistry.twins import build_twins


def test_closest_same_family_twin_wins():
    rows = [("A", f"{i:014d}XX", "Fam") for i in range(10)]                       # species A: 10 compounds
    rows += [("B", f"{i:014d}YY", "Fam") for i in range(8)] + [("B", "Z" * 14 + "AA", "Fam")]   # B shares 8 (stereo suffix differs)
    rows += [("C", f"{i:014d}XX", "Other") for i in range(10)]                    # same chemistry, wrong family -> excluded
    rows += [("D", f"{i:014d}XX", "Fam") for i in range(2)]                       # too few compounds -> excluded
    df = pd.DataFrame(rows, columns=["taxon", "inchikey", "family"])
    out = build_twins(df, ["A"], {"A": "Fam"})
    assert list(out.twin) == ["B"] and out.similarity[0] == round(8 / 11, 3)
