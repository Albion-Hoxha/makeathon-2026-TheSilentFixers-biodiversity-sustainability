"""Dashboard. Run: streamlit run app/app.py. Uses outputs/risk.csv + twins.csv, falls back to the sample_* files."""
import os, pandas as pd, streamlit as st

def load(name):
    real, sample = f"outputs/{name}.csv", f"outputs/sample_{name}.csv"
    if os.path.exists(real):
        return pd.read_csv(real), False
    return pd.read_csv(sample), True

risk, fake_r = load("risk")
twins, fake_t = load("twins")
st.title("Vanishing Apothecary")
if fake_r or fake_t:
    st.warning("SAMPLE DATA: placeholder numbers, not results. Add outputs/risk.csv and outputs/twins.csv.")
sp = st.selectbox("Species", risk.species)
r = risk[risk.species == sp].iloc[0]
c1, c2, c3 = st.columns(3)
c1.metric("Suitable area now (km²)", f"{r.area_now_km2:,.0f}")
c2.metric("Suitable area 2050 (km²)", f"{r.area_2050_km2:,.0f}")
c3.metric("Habitat loss", f"{r.loss_pct:.0f}%")
st.subheader("Chemical twins (research candidates, not medical substitutes)")
st.dataframe(twins[twins.species == sp], hide_index=True)
for img in (f"outputs/maps/{sp}_now.png", f"outputs/maps/{sp}_2050.png"):
    if os.path.exists(img):
        st.image(img)
