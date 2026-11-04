"""Vanishing Apothecary dashboard. Run: streamlit run app/app.py
Reads outputs/risk.csv, risk_scenarios.csv (optional), twins.csv; falls back to outputs/sample_*.csv with a visible banner.
Every number shown comes from those files; nothing is hardcoded."""
import json, math, os, sys
from pathlib import Path
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import theme as T
from src.chemistry.ema import ema_label, load_ema
from src.config import AUTHORITY, DATA_GAP, FAMILY

OUT = Path(os.environ.get("VA_OUTPUTS", ROOT / "outputs"))
LOW, HIGH = 10, 30  # our own convention: projected loss % below LOW = Low, below HIGH = Medium, else High
COMMON = {"Salvia officinalis": "Common sage", "Gentiana lutea": "Yellow gentian", "Arnica montana": "Mountain arnica",
          "Origanum vulgare": "Oregano", "Hypericum perforatum": "St John's wort"}
COLOR = {"Low": "#48D98D", "Medium": "#E9C66C", "High": "#E4694F", "n/a": "#8FB5A3"}
PAGES = ["Overview", "Species Explorer", "Climate Explorer", "Chemical Twins", "Risk Analytics", "Conservation", "Data & Methods"]
PAGE_ICONS = {
    "Overview": "✦", "Species Explorer": "❋", "Climate Explorer": "☼",
    "Chemical Twins": "⚗", "Risk Analytics": "⌁", "Conservation": "♧",
    "Data & Methods": "▤",
}

st.set_page_config(page_title="Vanishing Apothecary", layout="wide")
st.markdown(T.CSS, unsafe_allow_html=True)


def load(name, optional=False):
    real, sample = OUT / f"{name}.csv", OUT / f"sample_{name}.csv"
    if real.exists():
        return pd.read_csv(real), False
    if optional:
        return None, False
    return pd.read_csv(sample), True


def need(df, cols, name):
    miss = [c for c in cols if c not in df.columns]
    if miss:
        st.error(f"{name} is missing columns: {', '.join(miss)}")
        st.stop()


def risk_class(loss):
    return "n/a" if pd.isna(loss) else "Low" if loss < LOW else "Medium" if loss < HIGH else "High"


risk, fake_r = load("risk")
twins, fake_t = load("twins")
scen, _ = load("risk_scenarios", optional=True)
need(risk, ["species", "n_records", "area_now_km2", "area_2050_km2", "loss_pct", "auc"], "risk.csv")
need(twins, ["species", "twin", "similarity"], "twins.csv")
for c in ["n_records", "area_now_km2", "area_2050_km2", "loss_pct", "auc"]:
    risk[c] = pd.to_numeric(risk[c], errors="coerce")
twins["similarity"] = pd.to_numeric(twins["similarity"], errors="coerce")
if "twin_iucn_status" not in twins:
    twins["twin_iucn_status"] = "not assessed"
twins["twin_iucn_status"] = twins["twin_iucn_status"].fillna("not assessed")
if "ema_evidence" not in twins:  # older twins.csv / sample file
    twins["ema_evidence"] = "n/a"
EMA = load_ema()
risk["cls"] = risk.loss_pct.map(risk_class)

@st.cache_data
def load_lotus_sets(path):
    p = Path(path)
    if not p.exists():
        return {}
    compounds = pd.read_csv(p, usecols=["taxon", "inchikey"])
    compounds["skeleton"] = compounds.inchikey.astype(str).str[:14]
    return compounds.groupby("taxon").skeleton.agg(lambda values: set(values)).to_dict()

LOTUS_SETS = load_lotus_sets(str(ROOT / "data" / "lotus_compounds.csv"))

# ---- sidebar
with st.sidebar:
    st.markdown('<div class="brand">VANISHING<br>APOTHECARY<small>BALKAN BOTANICAL INTELLIGENCE</small></div>', unsafe_allow_html=True)
    if "current_page" not in st.session_state or st.session_state.current_page not in PAGES:
        st.session_state.current_page = PAGES[0]
    st.markdown('<div class="side-label">EXPLORE THE PROJECT</div>', unsafe_allow_html=True)
    for nav_page in PAGES:
        st.button(
            f"{PAGE_ICONS[nav_page]}   {nav_page}",
            key=f"nav_{nav_page}",
            type="primary" if st.session_state.current_page == nav_page else "secondary",
            use_container_width=True,
            on_click=lambda selected=nav_page: setattr(st.session_state, "current_page", selected),
        )
    page = st.session_state.current_page
    st.markdown('<div class="side-label species-label">FOCAL PLANT</div>', unsafe_allow_html=True)
    sp = st.selectbox("Species", list(risk.species))
    st.markdown('<div class="quote">Discover what disappears.<br>Understand what remains.</div>', unsafe_allow_html=True)
r = risk[risk.species == sp].iloc[0]
tw = twins[twins.species == sp].sort_values("similarity", ascending=False)

if fake_r or fake_t:
    st.warning("SAMPLE DATA: placeholder numbers, not results. Add outputs/risk.csv and outputs/twins.csv.")


def panel(title):
    c = st.container(border=True, key="panel_" + "".join(ch for ch in title.lower() if ch.isalnum()))
    c.markdown(f'<h4 class="ph">{T.e(title)}</h4>', unsafe_allow_html=True)
    return c


def fmt(x, f="{:.0f}", suffix=""):
    return "—" if pd.isna(x) else f.format(x) + suffix


def species_card(r, show_bars=True):
    img = T.img_data(ROOT / "app" / "assets" / "species" / f"{r.species}.jpg")
    g, s = r.species.split()[0][0], r.species.split()[-1][0]
    pic = f'<img class="avatar" src="{img}">' if img else f'<div class="avatar">{g}.{s}.</div>'
    direction = "gain" if r.loss_pct < 0 else "loss"
    magnitude = abs(r.loss_pct)
    change_color = COLOR["Low"] if r.loss_pct < 0 else COLOR[r.cls]
    bars = (T.bar(f"Projected area {direction}", min(magnitude, 100), f"{magnitude:.1f}% {direction}", change_color) +
            T.bar("Model AUC (spatial CV)", r.auc * 100, fmt(r.auc, "{:.2f}"))) if show_bars else ""
    fam = FAMILY.get(r.species, "—")
    return (f'<div class="card"><div class="row">{pic}<div><div class="sci">{T.e(r.species)} <span class="auth">{T.e(AUTHORITY.get(r.species, ""))}</span></div>'
            f'<p>{T.e(COMMON.get(r.species, ""))} · {T.e(fam)} {T.badge(r.cls)}</p>'
            f'<p>EU herbal monograph (EMA): {T.e(ema_label(r.species, EMA))}</p>'
            f'<p>{fmt(r.n_records)} GBIF records · {fmt(r.area_now_km2, "{:,.0f}")} km² suitable now → {fmt(r.area_2050_km2, "{:,.0f}")} km² in 2041–2060</p>{bars}</div></div></div>')


def occurrences():
    for p in (ROOT / "data" / "occurrences.csv", ROOT / "app" / "assets" / "occurrences.csv"):
        if p.exists():
            return pd.read_csv(p)


def occ_map(sp_):
    d = occurrences()
    d = d[d.species == sp_] if d is not None else None
    if d is None or d.empty:
        st.markdown('<div class="empty">No GBIF records bundled for this species.</div>', unsafe_allow_html=True)
        return
    fig = go.Figure(go.Scattermap(lat=d.lat, lon=d.lon, mode="markers", marker=dict(size=6, color="#20C979", opacity=.65), hoverinfo="skip"))
    fig.update_layout(map=dict(style="carto-darkmatter", center=dict(lat=43.2, lon=19.5), zoom=5))
    st.plotly_chart(T.style(fig, 430), use_container_width=True)
    st.caption(f"{len(d):,} observed GBIF records (CC0 / CC-BY, downloaded 2026-11-04). These are observations, not modelled habitat.")


def maps(sp_):
    t1, t2 = st.tabs(["Observed records (GBIF)", "Modelled habitat"])
    with t1:
        occ_map(sp_)
    with t2:
        a, b = OUT / "maps" / f"{sp_}_now.png", OUT / "maps" / f"{sp_}_2050.png"
        if a.exists() and b.exists():
            c1, c2 = st.columns(2)
            c1.image(str(a), caption="Suitable habitat, current climate")
            c2.image(str(b), caption="2041–2060: share of scenarios calling the cell suitable")
        else:
            st.markdown('<div class="empty">Modelled maps appear after <code>python -m src.climate.sdm</code> has run for this species.</div>', unsafe_allow_html=True)


def network(sp_, tw_):
    fig = go.Figure()
    if len(tw_):
        ang = [2 * math.pi * i / len(tw_) for i in range(len(tw_))]
        xs, ys = [math.cos(a) for a in ang], [math.sin(a) for a in ang]
        for x, y in zip(xs, ys):
            fig.add_trace(go.Scatter(x=[0, x], y=[0, y], mode="lines", line=dict(color="#1f6b58", width=1.5), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers+text", text=list(tw_.twin), textposition="top center", showlegend=False,
                                 marker=dict(size=[14 + 30 * (s if s == s else 0) for s in tw_.similarity], color="#20C979", line=dict(color="#9ACD9B", width=1)),
                                 hovertext=[f"{t}: Jaccard {s:.2f}" for t, s in zip(tw_.twin, tw_.similarity)], hoverinfo="text"))
    fig.add_trace(go.Scatter(x=[0], y=[0], mode="markers+text", text=[sp_], textposition="bottom center", showlegend=False,
                             marker=dict(size=34, color="#D9B85F"), hoverinfo="skip"))
    fig.update_xaxes(visible=False, range=[-1.6, 1.6]).update_yaxes(visible=False, range=[-1.5, 1.5])
    return T.style(fig, 340)


def ranking(tw_):
    if not len(tw_):
        return '<div class="empty">No twins computed for this species (too few compounds in LOTUS).</div>'
    return "".join(f'<div class="rank"><span>{i}. <i class="sp">{T.e(t)}</i><br><small>EMA: {T.e(str(ev))} · IUCN: {T.e(str(st_))}</small></span><span>{fmt(s, "{:.2f}")}</span></div>'
                   for i, (t, s, st_, ev) in enumerate(zip(tw_.twin, tw_.similarity, tw_.twin_iucn_status, tw_.ema_evidence), 1))


def donut():
    counts = risk.cls.value_counts()
    fig = go.Figure(go.Pie(labels=list(counts.index), values=list(counts.values), hole=.62, sort=False,
                           marker=dict(colors=[COLOR[k] for k in counts.index]), textinfo="value"))
    fig.add_annotation(text=f"{len(risk)}<br>species", showarrow=False, font=dict(size=18))
    return T.style(fig, 260)


def loss_bars(col):
    d = risk.sort_values(col)
    fig = go.Figure(go.Bar(x=d[col], y=d.species, orientation="h", marker_color=[COLOR[c] for c in d.cls]))
    fig.add_vline(x=0, line_dash="dash", line_color="#D9B85F", opacity=.8)
    fig.update_xaxes(title="Projected change in suitable area, 2041–2060 (%) · negative = gain", gridcolor="#14473d", zeroline=False)
    return T.style(fig, 280)


# ---- pages
if page == "Overview":
    st.markdown(T.hero("VANISHING APOTHECARY", "Climate risk and chemical twins for Balkan medicinal plants", "Hackathon prototype",
                       T.img_data(ROOT / "app" / "assets" / "hero.jpg")), unsafe_allow_html=True)
    projected_losses = risk[risk.loss_pct > 0]
    worst = projected_losses.loc[projected_losses.loss_pct.idxmax()] if len(projected_losses) else None
    st.markdown(T.kpis([
        ("Species modelled", len(risk), "plants with enough data"),
        ("Mean projected area change", fmt(risk.loss_pct.mean(), "{:+.1f}", "%"), "2041–2060 · negative = gain"),
        ("Largest projected loss", worst.species if worst is not None else "None projected", fmt(worst.loss_pct if worst is not None else float("nan"), "{:.1f}", "% of suitable area")),
        ("Chemical twin pairs", len(twins), "Jaccard-ranked candidates"),
        ("Mean spatial-CV AUC", fmt(risk.auc.mean(), "{:.2f}"), "model skill on held-out regions")]), unsafe_allow_html=True)
    gains = int((risk.loss_pct < 0).sum())
    losses = int((risk.loss_pct > 0).sum())
    st.caption(f"Across the five species, the model projects suitable-area gains for {gains} and losses for {losses}. Area change is not a population trend or extinction probability.")
    a, b = st.columns([3, 2])
    with a:
        with panel("Habitat map: " + sp):
            maps(sp)
    with b:
        st.markdown(species_card(r), unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1, panel("Chemical twin network"):
        st.plotly_chart(network(sp, tw.head(5)), use_container_width=True)
        st.markdown(ranking(tw.head(5)), unsafe_allow_html=True)
    with c2, panel("Species risk overview"):
        st.plotly_chart(donut(), use_container_width=True)
        st.caption(f"Risk class from projected loss: Low < {LOW}%, Medium < {HIGH}%, High otherwise (our convention).")
    with c3:
        st.markdown(T.card("Conservation actions (potential)", "<p>Suggested follow-ups, not measured outcomes:</p>"
                       "<p>• Prioritise monitoring where projected loss is highest.</p><p>• Consider in-situ protection for high-loss species.</p>"
                       "<p>• Explore controlled cultivation as a research direction.</p>"), unsafe_allow_html=True)

elif page == "Species Explorer":
    st.header("Species Explorer")
    st.caption("See how modelled suitable area shifts from today to 2041–2060, alongside occurrence coverage and model performance.")
    compare_species = st.multiselect("Plants in this comparison", list(risk.species), default=list(risk.species), key="species_compare")
    compared = risk[risk.species.isin(compare_species)].sort_values("loss_pct", ascending=False)
    if len(compared):
        mean_change = -compared.loss_pct.mean()
        direction = "gain" if mean_change >= 0 else "loss"
        gains = int((compared.loss_pct < 0).sum())
        losses = int((compared.loss_pct > 0).sum())
        st.markdown(T.kpis([
            ("Plants compared", len(compared), "of 5 focal species"),
            ("GBIF observations", f"{compared.n_records.sum():,.0f}", "records across selection"),
            ("Average modelled change", f"{abs(mean_change):.1f}% {direction}", "negative risk-file values mean gains"),
            ("Projected direction", f"{gains} gain · {losses} loss", "based on modelled suitable area")
        ]), unsafe_allow_html=True)

        fig = go.Figure()
        for row in compared.itertuples():
            connector_color = COLOR["Low"] if row.loss_pct < 0 else COLOR["High"]
            fig.add_trace(go.Scatter(x=[row.area_now_km2, row.area_2050_km2], y=[row.species, row.species],
                                     mode="lines", line=dict(color=connector_color, width=3), hoverinfo="skip", showlegend=False))
        fig.add_trace(go.Scatter(x=compared.area_now_km2, y=compared.species, mode="markers", name="Current",
                                 marker=dict(size=15, color="#20C979", line=dict(color="#d8f4e3", width=1)),
                                 customdata=compared.n_records,
                                 hovertemplate="%{y}<br>Current suitable area: %{x:,.0f} km²<br>GBIF records: %{customdata:,}<extra></extra>"))
        future_text = [f"{abs(v):.0f}% {'gain' if v < 0 else 'loss'}" for v in compared.loss_pct]
        fig.add_trace(go.Scatter(x=compared.area_2050_km2, y=compared.species, mode="markers+text", name="2041–2060",
                                 text=future_text, textposition="middle right", cliponaxis=False,
                                 marker=dict(size=17, symbol="diamond", color="#D9B85F", line=dict(color="#fff0bd", width=1)),
                                 customdata=compared.loss_pct,
                                 hovertemplate="%{y}<br>2041–2060 suitable area: %{x:,.0f} km²<br>Loss-positive index: %{customdata:+.1f}%<extra></extra>"))
        fig.update_layout(title="Suitable habitat: current climate → 2041–2060", xaxis_title="Modelled suitable area (km²)", yaxis_title="",
                          showlegend=True, legend=dict(orientation="h", y=1.08, x=0), margin=dict(r=110))
        fig.update_xaxes(range=[0, compared[["area_now_km2", "area_2050_km2"]].to_numpy().max() * 1.45], gridcolor="#14473d")
        st.plotly_chart(T.style(fig, max(320, 64 * len(compared))), use_container_width=True)
        st.caption("Teal dot = current modelled area · gold diamond = future area · connector color shows direction (green = gain, coral = loss). These are suitability projections, not population forecasts.")
        comp_table = compared[["species", "n_records", "area_now_km2", "area_2050_km2", "loss_pct", "auc"]].rename(columns={
            "n_records": "GBIF records", "area_now_km2": "Suitable now (km²)", "area_2050_km2": "Suitable 2041–2060 (km²)",
            "loss_pct": "Area change (%)", "auc": "Spatial-CV AUC"})
        with st.expander("View detailed comparison values"):
            st.dataframe(comp_table, hide_index=True, use_container_width=True)
    else:
        st.info("Choose at least one plant to compare.")
    st.markdown('<div class="grid">' + "".join(species_card(x) for x in risk.itertuples()) + "</div>", unsafe_allow_html=True)
    st.subheader(sp)
    maps(sp)

elif page == "Climate Explorer":
    st.header("Climate Explorer")
    st.caption("WorldClim CMIP6, period 2041–2060 (not yearly values). Habitat = Random Forest suitability above a 10th-percentile threshold. Negative area change means a modelled gain.")
    if scen is not None and len(scen):
        choices = {"Mean across all 6 GCM runs": None, "SSP2-4.5 · mean across GCMs": "ssp245", "SSP5-8.5 · mean across GCMs": "ssp585"}
        pick = st.selectbox("Climate projection", list(choices))
        prefix = choices[pick]
        selected_runs = scen if prefix is None else scen[scen.scenario.str.startswith(prefix)]
        d = selected_runs.groupby("species").loss_pct.mean()
        risk["scenario_loss"] = risk.species.map(d)
        risk["cls"] = risk.scenario_loss.map(risk_class)
        col = "scenario_loss"
        rng = selected_runs[selected_runs.species == sp].sort_values("loss_pct")
        if len(rng):
            st.info(f"{sp}: projected area change ranges from {rng.loss_pct.min():+.1f}% to {rng.loss_pct.max():+.1f}% across {len(rng)} GCM runs; negative values are gains.")
            run_labels = rng.scenario.str.replace("ssp245", "SSP2-4.5", regex=False).str.replace("ssp585", "SSP5-8.5", regex=False).str.replace("_", " · ", regex=False)
            fig = go.Figure(go.Bar(x=rng.loss_pct, y=run_labels, orientation="h",
                                   marker_color=[COLOR["Low"] if v < 0 else COLOR[risk_class(v)] for v in rng.loss_pct],
                                   hovertemplate="%{y}<br>Area change: %{x:.1f}%<extra></extra>"))
            fig.add_vline(x=0, line_dash="dash", line_color="#D9B85F")
            fig.update_layout(title=f"GCM range for {sp}", xaxis_title="Projected suitable-area change (%)", yaxis_title="", showlegend=False)
            st.plotly_chart(T.style(fig, max(230, 42 * len(rng))), use_container_width=True)
    else:
        st.info("Per-scenario results (risk_scenarios.csv) appear after the climate model has run.")
        col = "loss_pct"
    st.plotly_chart(loss_bars(col), use_container_width=True)
    maps(sp)

elif page == "Chemical Twins":
    st.header("Chemical Twins")
    st.warning("Chemical similarity does not establish equal medicinal efficacy or safety. Twins are research candidates only.")
    a, b = st.columns([3, 2])
    a.plotly_chart(network(sp, tw), use_container_width=True)
    b.markdown(T.card("Top similar species (Jaccard)", ranking(tw)), unsafe_allow_html=True)
    focal_set = LOTUS_SETS.get(sp, set())
    twin_details = tw.copy()
    twin_details["shared_skeletons"] = [len(focal_set & LOTUS_SETS.get(t, set())) for t in twin_details.twin]
    twin_details["twin_lotus_skeletons"] = [len(LOTUS_SETS.get(t, set())) for t in twin_details.twin]
    twin_details = twin_details.rename(columns={"species": "Focal species", "twin": "Candidate twin", "similarity": "Jaccard similarity",
                                                "shared_skeletons": "Shared chemical skeletons", "twin_lotus_skeletons": "Twin LOTUS coverage",
                                                "ema_evidence": "EMA evidence", "twin_iucn_status": "IUCN status"})
    st.caption(f"{sp}: {len(focal_set)} distinct LOTUS chemical skeletons. Jaccard = shared skeletons ÷ all unique skeletons across the pair; rankings require at least 5 skeletons per species.")
    st.dataframe(twin_details, hide_index=True, use_container_width=True)
    with st.expander("View shared chemical-skeleton identifiers"):
        if not focal_set:
            st.info("LOTUS compound data are unavailable for the selected plant.")
        else:
            for twin_name in tw.twin:
                shared = sorted(focal_set & LOTUS_SETS.get(twin_name, set()))
                st.markdown(f"**{twin_name}:** {', '.join(shared[:8]) if shared else 'No shared identifiers found in the local LOTUS file'}")
            st.caption("Identifiers are the first 14 characters of InChIKeys, used by the pipeline to group stereoisomers. The file does not include readable compound names.")

elif page == "Risk Analytics":
    st.header("Risk Analytics")
    st.dataframe(risk[["species", "cls", "n_records", "area_now_km2", "area_2050_km2", "loss_pct", "auc"]].rename(columns={"cls": "risk class"}), hide_index=True)
    st.caption("AUC is computed on held-out 1-degree spatial blocks. Values near 0.5 indicate little discrimination; record count is a data-coverage indicator, not a guarantee of model quality.")
    fig = go.Figure()
    for cls in [c for c in ["Low", "Medium", "High", "n/a"] if c in set(risk.cls)]:
        d = risk[risk.cls == cls]
        fig.add_trace(go.Scatter(x=d.n_records, y=d.auc, mode="markers", customdata=d.species,
                                 name=cls, marker=dict(size=13, color=COLOR[cls], line=dict(color="#d7eee0", width=1)),
                                 hovertemplate="%{customdata}<br>GBIF records: %{x:,}<br>Spatial-CV AUC: %{y:.3f}<extra></extra>"))
    fig.add_hline(y=.5, line_dash="dash", line_color="#D9B85F", annotation_text="AUC = 0.5 baseline")
    fig.update_layout(title="Occurrence coverage and held-out model performance", xaxis_title="GBIF records used", yaxis_title="Spatial-block CV AUC", showlegend=False)
    st.plotly_chart(T.style(fig, 380), use_container_width=True)
    st.plotly_chart(loss_bars("loss_pct"), use_container_width=True)

elif page == "Conservation":
    st.header("Conservation")
    st.info("This is a screening view, not a conservation-status assessment. The model identifies projected suitable-area change; it does not measure population trends, harvest pressure or whether an action works.")
    st.dataframe(risk.sort_values("loss_pct", ascending=False)[["species", "cls", "loss_pct", "n_records"]].rename(columns={
        "cls": "screening category", "loss_pct": "Area change index (%) · positive = loss", "n_records": "GBIF records"}), hide_index=True, use_container_width=True)
    st.warning("Protected-area overlap is not calculated: WDPA data are not integrated in this project yet. Do not interpret this page as showing how much habitat is protected.")
    st.markdown('<div class="grid">' + T.card("Monitor", "<p>Prioritise field monitoring where projected loss is highest.</p>") +
                T.card("Protect", "<p>Check overlap with protected areas. WDPA overlay is not integrated yet.</p>") +
                T.card("Cultivate", "<p>Controlled cultivation is a research direction, not a finding.</p>") + "</div>", unsafe_allow_html=True)

else:  # Data & Methods
    st.header("Data & Methods")
    g = DATA_GAP.get("Sideritis scardica", {})
    lotus_counts = {species: len(LOTUS_SETS.get(species, set())) for species in risk.species}
    coverage = risk[["species", "n_records", "auc", "loss_pct"]].copy()
    coverage["LOTUS skeletons"] = coverage.species.map(lotus_counts)
    coverage = coverage.rename(columns={"species": "Species", "n_records": "GBIF records", "auc": "Spatial-CV AUC", "loss_pct": "Area change index (%) · positive = loss"})
    st.caption("Project data snapshot: 4 November 2026. Climate projections represent 2041–2060.")
    st.dataframe(coverage, hide_index=True, use_container_width=True)
    with st.expander("Data sources and licences", expanded=True):
        st.markdown("| Data | Source | Licence |\n|---|---|---|\n| Occurrences | GBIF | CC0 / CC-BY |\n| Climate | WorldClim 2.1 (CMIP6) | CC-BY 4.0 |\n"
                    "| Natural products | LOTUS via Wikidata | CC0 |\n| Conservation context | IUCN, WDPA (not integrated yet) | non-commercial terms, cite |")
    with st.expander("Methods"):
        st.markdown("- GBIF records cleaned (coordinate uncertainty < 5 km, duplicates removed, one record per 2.5 arc-minute cell).\n"
                    "- Random Forest presence/background model on WorldClim bioclimatic variables; AUC from 1-degree spatial block cross-validation.\n"
                    "- Projections for 2041–2060 under SSP2-4.5 and SSP5-8.5; threshold = 10th percentile of held-out presences.\n"
                    f"- Risk class from projected loss: Low < {LOW}%, Medium < {HIGH}%, High otherwise. This is our own convention, not an IUCN category.\n"
                    "- Chemical twins: Jaccard similarity of LOTUS compound sets (InChIKey skeleton), same plant family, species level only, at least 5 compounds each.")
    with st.expander("How to read the numbers"):
        st.markdown("- **Area change index:** `(current suitable area − future suitable area) ÷ current suitable area × 100`. Positive values mean modelled area loss; negative values mean modelled area gain. It is not a population trend or extinction probability.\n"
                    "- **AUC:** discrimination between presence and background records on held-out spatial blocks; 0.5 is approximately chance-level.\n"
                    "- **Jaccard similarity:** shared LOTUS chemical skeletons divided by all unique skeletons across the pair. It measures database overlap, not therapeutic equivalence.\n"
                    "- **LOTUS coverage:** unique 14-character InChIKey skeletons found in the downloaded dataset; a low count can make the twin ranking incomplete.")
    with st.expander("EU herbal monograph evidence (EMA)"):
        st.markdown("For each plant we show whether the European Medicines Agency's committee on herbal medicines (HMPC) has published an EU herbal monograph: "
                    "**well-established use** (sufficient safety and efficacy data) or **traditional use** (sufficient safety data and plausible efficacy from long-standing use). "
                    "This describes the *plant*, not the chemical similarity: a twin with a monograph is not shown to be a substitute, and traditional use is not clinical proof. "
                    "\"No EU monograph\" means none in the EMA overview EMA/HMPC/228356/2012 Rev. 2 (March 2023) for the plant families we use, so newer monographs may be missing. "
                    "Botanical names were checked against each EMA herbal page. Table: `data/ema_monographs.csv`.")
    with st.expander("Why Sideritis scardica is not modelled"):
        st.markdown(f"On 2026-11-04 GBIF had {g.get('gbif_records_in_region', '?')} records in our region ({g.get('usable_after_filters', '?')} usable after filters, minimum 30) "
                    f"and LOTUS only {g.get('lotus_compounds', '?')} compounds (minimum 5). It is reported as **insufficient data**, not as a modelled species. "
                    "(It does have an EU traditional-use herbal monograph, so the gap is in occurrence and chemistry data, not in interest.)")
    with st.expander("Limitations"):
        st.markdown("GBIF sampling bias; climate-model disagreement (see scenario ranges); habitat suitability is not abundance or extinction risk; "
                    "chemical similarity is not medicinal equivalence. Nothing here is medical advice.")
    credits = ROOT / "app" / "assets" / "credits.json"
    if credits.exists():
        with st.expander("Photo credits (Wikimedia Commons)"):
            for k, v in json.loads(credits.read_text()).items():
                if v:
                    st.markdown(f"- **{k}**: {v['author']}, {v['licence']}, [{v['title']}]({v['page']})")
    with st.expander("AI usage"):
        st.markdown("Claude (Anthropic) and GitHub Copilot assisted with code and documentation. The team reviews all results.")
    st.code("python -m src.climate.fetch_gbif\npython -m src.climate.sdm\npython -m src.chemistry.twins\nstreamlit run app/app.py", language="bash")
