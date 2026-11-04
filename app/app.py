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
from src.config import DATA_GAP, FAMILY

OUT = Path(os.environ.get("VA_OUTPUTS", ROOT / "outputs"))
LOW, HIGH = 10, 30  # our own convention: projected loss % below LOW = Low, below HIGH = Medium, else High
COMMON = {"Salvia officinalis": "Common sage", "Gentiana lutea": "Yellow gentian", "Arnica montana": "Mountain arnica",
          "Origanum vulgare": "Oregano", "Hypericum perforatum": "St John's wort"}
COLOR = {"Low": "#48D98D", "Medium": "#E9C66C", "High": "#E4694F", "n/a": "#8FB5A3"}
PAGES = ["Overview", "Species Explorer", "Climate Explorer", "Chemical Twins", "Risk Analytics", "Conservation", "Data & Methods"]

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
risk["cls"] = risk.loss_pct.map(risk_class)

# ---- sidebar
with st.sidebar:
    st.markdown('<div class="brand">VANISHING<br>APOTHECARY<small>BALKAN BOTANICAL INTELLIGENCE</small></div>', unsafe_allow_html=True)
    page = st.radio("Navigate", PAGES, label_visibility="collapsed")
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
    bars = (T.bar("Habitat retained 2041–2060", 100 - r.loss_pct, fmt(100 - r.loss_pct, suffix="%")) +
            T.bar("Projected habitat loss", r.loss_pct, fmt(r.loss_pct, suffix="%"), COLOR[r.cls]) +
            T.bar("Model AUC (spatial CV)", r.auc * 100, fmt(r.auc, "{:.2f}"))) if show_bars else ""
    fam = FAMILY.get(r.species, "—")
    return (f'<div class="card"><div class="row">{pic}<div><div class="sci">{T.e(r.species)}</div>'
            f'<p>{T.e(COMMON.get(r.species, ""))} · {T.e(fam)} {T.badge(r.cls)}</p>'
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
    return "".join(f'<div class="rank"><span>{i}. {T.e(t)}</span><span>{fmt(s, "{:.2f}")} <i>{T.e(str(st_))}</i></span></div>'
                   for i, (t, s, st_) in enumerate(zip(tw_.twin, tw_.similarity, tw_.twin_iucn_status), 1))


def donut():
    counts = risk.cls.value_counts()
    fig = go.Figure(go.Pie(labels=list(counts.index), values=list(counts.values), hole=.62, sort=False,
                           marker=dict(colors=[COLOR[k] for k in counts.index]), textinfo="value"))
    fig.add_annotation(text=f"{len(risk)}<br>species", showarrow=False, font=dict(size=18))
    return T.style(fig, 260)


def loss_bars(col):
    d = risk.sort_values(col)
    fig = go.Figure(go.Bar(x=d[col], y=d.species, orientation="h", marker_color=[COLOR[c] for c in d.cls]))
    fig.update_xaxes(title="Projected habitat loss, 2041–2060 (%)", gridcolor="#14473d")
    return T.style(fig, 280)


# ---- pages
if page == "Overview":
    st.markdown(T.hero("VANISHING APOTHECARY", "Climate risk and chemical twins for Balkan medicinal plants", "Hackathon prototype",
                       T.img_data(ROOT / "app" / "assets" / "hero.jpg")), unsafe_allow_html=True)
    worst = risk.loc[risk.loss_pct.idxmax()] if risk.loss_pct.notna().any() else None
    st.markdown(T.kpis([
        ("Species modelled", len(risk), "plants with enough data"),
        ("Mean projected habitat loss", fmt(risk.loss_pct.mean(), "{:.1f}", "%"), "2041–2060, mean of scenarios"),
        ("Largest projected loss", worst.species if worst is not None else "—", fmt(worst.loss_pct if worst is not None else float("nan"), "{:.0f}", "% of suitable area")),
        ("Chemical twin pairs", len(twins), "Jaccard-ranked candidates"),
        ("Mean spatial-CV AUC", fmt(risk.auc.mean(), "{:.2f}"), "model skill on held-out regions")]), unsafe_allow_html=True)
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
    st.markdown('<div class="grid">' + "".join(species_card(x) for x in risk.itertuples()) + "</div>", unsafe_allow_html=True)
    st.subheader(sp)
    maps(sp)

elif page == "Climate Explorer":
    st.header("Climate Explorer")
    st.caption("WorldClim CMIP6, period 2041–2060 (not yearly values). Habitat = Random Forest suitability above a 10th-percentile threshold.")
    col = "loss_pct"
    if scen is not None and len(scen):
        pick = st.selectbox("Scenario", ["Mean of scenarios"] + sorted(scen.scenario.unique()))
        if pick != "Mean of scenarios":
            d = scen[scen.scenario == pick].set_index("species").loss_pct
            risk["scenario_loss"] = risk.species.map(d)
            risk["cls"] = risk.scenario_loss.map(risk_class)
            col = "scenario_loss"
        rng = scen[scen.species == sp].loss_pct
        if len(rng):
            st.info(f"{sp}: projected loss ranges {rng.min():.0f}% to {rng.max():.0f}% across {len(rng)} scenario/GCM runs.")
    else:
        st.info("Per-scenario results (risk_scenarios.csv) appear after the climate model has run.")
    st.plotly_chart(loss_bars(col), use_container_width=True)
    maps(sp)

elif page == "Chemical Twins":
    st.header("Chemical Twins")
    st.warning("Chemical similarity does not establish equal medicinal efficacy or safety. Twins are research candidates only.")
    a, b = st.columns([3, 2])
    a.plotly_chart(network(sp, tw), use_container_width=True)
    b.markdown(T.card("Top similar species (Jaccard)", ranking(tw)), unsafe_allow_html=True)
    lotus = ROOT / "data" / "lotus_compounds.csv"
    if lotus.exists():
        comp = pd.read_csv(lotus)
        sets = comp.assign(k=comp.inchikey.str[:14]).groupby("taxon").k.agg(set)
        if sp in sets:
            st.caption(f"{sp}: {len(sets[sp])} distinct compounds in LOTUS. Shared with twins: " +
                       ", ".join(f"{t} {len(sets[sp] & sets[t])}" for t in tw.twin if t in sets))
    st.dataframe(tw, hide_index=True)

elif page == "Risk Analytics":
    st.header("Risk Analytics")
    st.dataframe(risk[["species", "cls", "n_records", "area_now_km2", "area_2050_km2", "loss_pct", "auc"]].rename(columns={"cls": "risk class"}), hide_index=True)
    st.caption("AUC is computed on held-out 1-degree spatial blocks. Values near 0.5 mean no skill. Low record counts make a species less reliable.")
    st.plotly_chart(loss_bars("loss_pct"), use_container_width=True)

elif page == "Conservation":
    st.header("Conservation")
    st.info("Model findings (the table) are separate from suggested actions (the cards). The model does not measure whether any action works.")
    st.dataframe(risk.sort_values("loss_pct", ascending=False)[["species", "cls", "loss_pct"]].rename(columns={"cls": "suggested monitoring priority"}), hide_index=True)
    st.markdown('<div class="grid">' + T.card("Monitor", "<p>Prioritise field monitoring where projected loss is highest.</p>") +
                T.card("Protect", "<p>Check overlap with protected areas. WDPA overlay is not integrated yet.</p>") +
                T.card("Cultivate", "<p>Controlled cultivation is a research direction, not a finding.</p>") + "</div>", unsafe_allow_html=True)

else:  # Data & Methods
    st.header("Data & Methods")
    g = DATA_GAP.get("Sideritis scardica", {})
    with st.expander("Data sources and licences", expanded=True):
        st.markdown("| Data | Source | Licence |\n|---|---|---|\n| Occurrences | GBIF | CC0 / CC-BY |\n| Climate | WorldClim 2.1 (CMIP6) | CC-BY 4.0 |\n"
                    "| Natural products | LOTUS via Wikidata | CC0 |\n| Conservation context | IUCN, WDPA (not integrated yet) | non-commercial terms, cite |")
    with st.expander("Methods"):
        st.markdown("- GBIF records cleaned (coordinate uncertainty < 5 km, duplicates removed, one record per 2.5 arc-minute cell).\n"
                    "- Random Forest presence/background model on WorldClim bioclimatic variables; AUC from 1-degree spatial block cross-validation.\n"
                    "- Projections for 2041–2060 under SSP2-4.5 and SSP5-8.5; threshold = 10th percentile of held-out presences.\n"
                    f"- Risk class from projected loss: Low < {LOW}%, Medium < {HIGH}%, High otherwise. This is our own convention, not an IUCN category.\n"
                    "- Chemical twins: Jaccard similarity of LOTUS compound sets (InChIKey skeleton), same plant family, at least 5 compounds each.")
    with st.expander("Why Sideritis scardica is not modelled"):
        st.markdown(f"On 2026-11-04 GBIF had {g.get('gbif_records_in_region', '?')} records in our region ({g.get('usable_after_filters', '?')} usable after filters, minimum 30) "
                    f"and LOTUS only {g.get('lotus_compounds', '?')} compounds (minimum 5). It is reported as **insufficient data**, not as a modelled species.")
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
