import numpy as np, pandas as pd, rasterio
from rasterio.transform import from_origin
from src.climate import sdm
from src.config import BBOX, SPECIES


def _tif(path, arr):
    tf = from_origin(BBOX[0], BBOX[3], 0.05, 0.05)
    with rasterio.open(path, "w", driver="GTiff", height=arr.shape[1], width=arr.shape[2], count=arr.shape[0],
                       dtype="float32", crs="EPSG:4326", transform=tf, nodata=-9999) as d:
        d.write(arr.astype("float32"))


def test_warming_shrinks_cool_species(tmp_path):
    h, w = int((BBOX[3] - BBOX[1]) / 0.05), int((BBOX[2] - BBOX[0]) / 0.05)
    rng = np.random.default_rng(1)
    temp = 20 - 0.9 * np.arange(h)[:, None] * 0.05 * 10 + np.zeros((h, w)) + rng.normal(0, .3, (h, w))  # cooler to the south
    cur = np.stack([temp, rng.normal(0, 1, (h, w))])
    _tif(tmp_path / "cur.tif", cur); _tif(tmp_path / "future_test.tif", cur + np.array([3, 0])[:, None, None])
    cool = np.argwhere(temp < np.percentile(temp, 25))  # species lives in the coolest quarter
    pick = cool[rng.choice(len(cool), 400, replace=False)]
    lon, lat = BBOX[0] + (pick[:, 1] + .5) * 0.05, BBOX[3] - (pick[:, 0] + .5) * 0.05
    pd.DataFrame(dict(species=SPECIES[0], lon=lon, lat=lat)).to_csv(tmp_path / "occ.csv", index=False)
    sdm.run(str(tmp_path / "occ.csv"), str(tmp_path / "cur.tif"), str(tmp_path / "future_*.tif"), str(tmp_path / "out"))
    r = pd.read_csv(tmp_path / "out/risk.csv").iloc[0]
    assert r.auc > 0.8 and r.loss_pct > 10 and r.area_now_km2 > 0, r.to_dict()
