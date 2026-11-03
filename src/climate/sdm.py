"""Species distribution model: now vs 2050 -> outputs/risk.csv, outputs/risk_scenarios.csv, outputs/maps/*.png.

Inputs (multi-band GeoTIFFs, same band order, e.g. the 19 WorldClim bioclim variables):
  data/climate/current.tif
  data/climate/future_*.tif   one file per scenario/GCM (e.g. future_ssp245_<gcm>.tif)
Run: python -m src.climate.sdm
"""
import glob, os
import numpy as np, pandas as pd, rasterio
from rasterio.windows import from_bounds
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import GroupKFold
from src.config import BBOX, SPECIES

N_BG = 5000


def read_stack(path):
    """-> (bands, h, w) float32 with NaN for nodata, and the affine transform, cropped to BBOX."""
    with rasterio.open(path) as src:
        win = from_bounds(*BBOX, transform=src.transform)
        arr = src.read(window=win, masked=True).astype("float32").filled(np.nan)
        return arr, src.window_transform(win)


def cell_area_km2(tf, h, w):
    lat = tf.f + (np.arange(h) + 0.5) * tf.e
    return np.repeat((abs(tf.a) * 111.32 * np.cos(np.radians(lat)) * abs(tf.e) * 110.57)[:, None], w, axis=1)


def presence_cells(occ, tf, h, w):
    """One presence per raster cell (this is the spatial thinning)."""
    col = ((occ.lon - tf.c) / tf.a).astype(int)
    row = ((occ.lat - tf.f) / tf.e).astype(int)
    ok = (row >= 0) & (row < h) & (col >= 0) & (col < w)
    return np.unique(np.c_[row[ok], col[ok]], axis=0)


def fit_species(cur, tf, occ, seed=0):
    """-> model, threshold, spatial-CV AUC."""
    nb, h, w = cur.shape
    valid = ~np.isnan(cur).any(axis=0)
    pres = presence_cells(occ, tf, h, w)
    pres = pres[valid[pres[:, 0], pres[:, 1]]]
    rng = np.random.default_rng(seed)
    vr, vc = np.nonzero(valid)
    pick = rng.choice(len(vr), min(N_BG, len(vr)), replace=False)
    bg = np.c_[vr[pick], vc[pick]]
    cells = np.r_[pres, bg]
    y = np.r_[np.ones(len(pres)), np.zeros(len(bg))]
    X = cur[:, cells[:, 0], cells[:, 1]].T
    # 1-degree spatial blocks: neighbouring cells never sit in both train and test
    lon = tf.c + (cells[:, 1] + 0.5) * tf.a
    lat = tf.f + (cells[:, 0] + 0.5) * tf.e
    groups = np.floor(lon).astype(int) * 1000 + np.floor(lat).astype(int)
    mk = lambda: RandomForestClassifier(300, min_samples_leaf=5, class_weight="balanced", n_jobs=-1, random_state=seed)
    oof, aucs = np.full(len(y), np.nan), []
    for tr, te in GroupKFold(n_splits=min(5, len(set(groups)))).split(X, y, groups):
        if y[te].sum() == 0 or y[tr].sum() == 0 or y[te].sum() == len(te):
            continue
        m = mk().fit(X[tr], y[tr])
        oof[te] = m.predict_proba(X[te])[:, 1]
        aucs.append(roc_auc_score(y[te], oof[te]))
    thr = np.nanpercentile(oof[y == 1], 10)  # 10th percentile of held-out presences
    return mk().fit(X, y), thr, float(np.mean(aucs)) if aucs else float("nan")


def suitable(model, thr, stack):
    nb, h, w = stack.shape
    valid = ~np.isnan(stack).any(axis=0)
    out = np.zeros((h, w), bool)
    out[valid] = model.predict_proba(stack[:, valid].T)[:, 1] >= thr
    return out


def run(occ_path="data/occurrences.csv", cur_path="data/climate/current.tif",
        fut_glob="data/climate/future_*.tif", out="outputs"):
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    occ_all = pd.read_csv(occ_path)
    cur, tf = read_stack(cur_path)
    futs = {os.path.basename(p)[7:-4]: read_stack(p)[0] for p in sorted(glob.glob(fut_glob))}
    assert futs, f"no future rasters match {fut_glob}"
    area = cell_area_km2(tf, *cur.shape[1:])
    os.makedirs(f"{out}/maps", exist_ok=True)
    rows, scen = [], []
    for sp in SPECIES:
        occ = occ_all[occ_all.species == sp]
        if len(occ) < 30:
            print(f"SKIP {sp}: only {len(occ)} records"); continue
        model, thr, auc = fit_species(cur, tf, occ)
        now = suitable(model, thr, cur)
        fut = {k: suitable(model, thr, v) for k, v in futs.items()}
        a_now = area[now].sum()
        for k, f in fut.items():
            scen.append(dict(species=sp, scenario=k, area_2050_km2=area[f].sum(), loss_pct=100 * (1 - area[f].sum() / a_now)))
        a50 = float(np.mean([area[f].sum() for f in fut.values()]))
        rows.append(dict(species=sp, n_records=len(occ), area_now_km2=round(a_now), area_2050_km2=round(a50),
                         loss_pct=round(100 * (1 - a50 / a_now), 1), auc=round(auc, 3)))
        agree = np.mean([f for f in fut.values()], axis=0)  # share of scenarios calling the cell suitable
        for tag, grid in (("now", now.astype(float)), ("2050", agree)):
            plt.figure(figsize=(6, 4.5)); plt.imshow(np.ma.masked_where(grid == 0, grid), cmap="YlGn", vmin=0, vmax=1)
            plt.title(f"{sp} suitable habitat {tag}"); plt.axis("off")
            plt.savefig(f"{out}/maps/{sp}_{tag}.png", dpi=120, bbox_inches="tight"); plt.close()
    pd.DataFrame(rows).to_csv(f"{out}/risk.csv", index=False)
    pd.DataFrame(scen).round(1).to_csv(f"{out}/risk_scenarios.csv", index=False)
    print(pd.DataFrame(rows))


if __name__ == "__main__":
    run()
