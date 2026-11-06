import numpy as np, pandas as pd, rasterio
from rasterio.transform import from_origin
from src.climate import sdm
from src.config import BBOX, SPECIES


def _tif(path, arr):
    tf = from_origin(BBOX[0], BBOX[3], 0.05, 0.05)
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[1], width=arr.shape[2], count=arr.shape[0],
                       dtype="float32", crs="EPSG:4326", transform=tf, nodata=-9999) as d:
        d.write(arr.astype("float32"))


def _run(tmp_path, where, shift):
    """Species living where(temp) on a north-south temperature gradient; future = current + shift degrees. -> row of risk.csv"""
    h, w = int((BBOX[3] - BBOX[1]) / 0.05), int((BBOX[2] - BBOX[0]) / 0.05)
    rng = np.random.default_rng(1)
    temp = 20 - 0.9 * np.arange(h)[:, None] * 0.05 * 10 + np.zeros((h, w)) + rng.normal(0, .3, (h, w))  # cooler to the south
    cur = np.stack([temp, rng.normal(0, 1, (h, w))])
    _tif(tmp_path / "cur.tif", cur); _tif(tmp_path / "future_test.tif", cur + np.array([shift, 0])[:, None, None])
    home = np.argwhere(where(temp))
    pick = home[rng.choice(len(home), 400, replace=False)]
    lon, lat = BBOX[0] + (pick[:, 1] + .5) * 0.05, BBOX[3] - (pick[:, 0] + .5) * 0.05
    pd.DataFrame(dict(species=SPECIES[0], lon=lon, lat=lat)).to_csv(tmp_path / "occ.csv", index=False)
    sdm.run(str(tmp_path / "occ.csv"), str(tmp_path / "cur.tif"), str(tmp_path / "future_*.tif"), str(tmp_path / "out"))
    return pd.read_csv(tmp_path / "out/risk.csv").iloc[0]


def test_warming_shrinks_cool_species(tmp_path):
    r = _run(tmp_path, lambda t: t < np.percentile(t, 25), 3)  # lives in the coolest quarter
    assert r.auc > 0.8 and r.loss_pct > 10 and r.area_now_km2 > 0 and r.extrapolated_pct > 0, r.to_dict()


def test_no_climate_change_means_no_change(tmp_path):
    r = _run(tmp_path, lambda t: t < np.percentile(t, 25), 0)
    assert abs(r.loss_pct) < 1 and r.lost_km2 == 0 and r.gained_km2 == 0, r.to_dict()


def test_warm_species_does_not_get_runaway_gains_from_extrapolation(tmp_path):
    # Without the envelope guard a Random Forest calls every cell warmer than any presence "suitable" -> huge fake gain
    r = _run(tmp_path, lambda t: t > np.percentile(t, 75), 3)
    assert r.loss_pct > -10, r.to_dict()  # old code (no guard) gave about -21 here
    assert r.loss_pct_unguarded < r.loss_pct - 5, r.to_dict()  # the unguarded column must show the extrapolated gain
