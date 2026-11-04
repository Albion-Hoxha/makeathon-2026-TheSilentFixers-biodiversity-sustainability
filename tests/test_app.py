from pathlib import Path
import pandas as pd, pytest
from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app" / "app.py")
PAGES = ["Overview", "Species Explorer", "Climate Explorer", "Chemical Twins", "Risk Analytics", "Conservation", "Data & Methods"]


def run(page):
    at = AppTest.from_file(APP, default_timeout=60).run()
    at.sidebar.radio[0].set_value(page).run()
    assert not at.exception, [e.value for e in at.exception]
    return at


@pytest.mark.parametrize("page", PAGES)
def test_every_page_runs_on_sample_data(page, monkeypatch, tmp_path):
    monkeypatch.setenv("VA_OUTPUTS", str(Path(APP).parents[1] / "outputs"))  # repo has only sample_* files
    at = run(page)
    assert any("SAMPLE DATA" in w.value for w in at.warning)


@pytest.mark.parametrize("page", PAGES)
def test_real_files_replace_sample_and_drive_numbers(page, monkeypatch, tmp_path):
    pd.DataFrame({"species": ["Salvia officinalis", "Gentiana lutea"], "n_records": [500, 200], "area_now_km2": [9000, 4000],
                  "area_2050_km2": [7000, 1000], "loss_pct": [22.2, 75.0], "auc": [0.91, float("nan")]}).to_csv(tmp_path / "risk.csv", index=False)
    pd.DataFrame({"species": ["Salvia officinalis"], "twin": ["Salvia pratensis"], "similarity": [0.42],
                  "twin_iucn_status": ["not assessed"], "ema_evidence": ["traditional use"]}).to_csv(tmp_path / "twins.csv", index=False)
    pd.DataFrame({"species": ["Salvia officinalis"] * 2, "scenario": ["ssp245_a", "ssp585_a"], "area_2050_km2": [1, 1],
                  "loss_pct": [10.0, 30.0]}).to_csv(tmp_path / "risk_scenarios.csv", index=False)
    monkeypatch.setenv("VA_OUTPUTS", str(tmp_path))
    at = run(page)
    assert not at.warning or not any("SAMPLE DATA" in w.value for w in at.warning)
    if page == "Overview":
        assert any("48.6" in m.value for m in at.markdown)  # mean of 22.2 and 75.0
    if page == "Chemical Twins":
        assert any("EMA: traditional use" in m.value for m in at.markdown)
    if page == "Species Explorer":
        assert any("EU herbal monograph (EMA): traditional use" in m.value for m in at.markdown)  # Salvia, from the committed table
    at.sidebar.selectbox[0].select("Gentiana lutea").run()  # species without twins and with NaN AUC must not crash
    assert not at.exception


def test_bad_csv_stops_with_message(monkeypatch, tmp_path):
    pd.DataFrame({"species": ["x"]}).to_csv(tmp_path / "risk.csv", index=False)
    pd.DataFrame({"species": ["x"], "twin": ["y"], "similarity": [0.5]}).to_csv(tmp_path / "twins.csv", index=False)
    monkeypatch.setenv("VA_OUTPUTS", str(tmp_path))
    at = AppTest.from_file(APP, default_timeout=60).run()
    assert any("missing columns" in e.value for e in at.error)
