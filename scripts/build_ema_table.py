"""Build data/ema_monographs.csv: which species have an EU herbal monograph (EMA/HMPC), and of which kind.
Substance list + category (well-established / traditional) were read from the EMA overview EMA/HMPC/228356/2012 Rev. 2 (March 2023),
the botanical names are checked against each substance's EMA herbal page. Covers the plant families we use (Lamiaceae, Gentianaceae,
Asteraceae, Hypericaceae). Run: python scripts/build_ema_table.py"""
import html, re, sys, time
from pathlib import Path
import pandas as pd, requests

UA = {"User-Agent": "Mozilla/5.0 vanishing-apothecary-hackathon"}
OVERVIEW = "EMA/HMPC/228356/2012 Rev. 2 (March 2023)"
# (EMA substance, use category, botanical names the monograph covers)
ROWS = [
    ("Salviae officinalis folium", "traditional", ["Salvia officinalis"]),
    ("Gentianae radix", "traditional", ["Gentiana lutea"]),
    ("Arnicae flos", "traditional", ["Arnica montana"]),
    ("Hyperici herba", "both", ["Hypericum perforatum"]),
    ("Sideritis herba", "traditional", ["Sideritis scardica", "Sideritis raeseri", "Sideritis syriaca", "Sideritis clandestina"]),
    ("Rosmarini folium", "traditional", ["Rosmarinus officinalis"]),
    ("Melissae folium", "traditional", ["Melissa officinalis"]),
    ("Origani dictamni herba", "traditional", ["Origanum dictamnus"]),
    ("Origani majoranae herba", "traditional", ["Origanum majorana"]),
    ("Menthae piperitae folium", "both", ["Mentha × piperita"]),  # peppermint oil has a well-established-use monograph too
    ("Lavandulae flos", "traditional", ["Lavandula angustifolia"]),
    ("Thymi herba", "traditional", ["Thymus vulgaris", "Thymus zygis"]),
    ("Marrubii herba", "traditional", ["Marrubium vulgare"]),
    ("Leonuri cardiacae herba", "traditional", ["Leonurus cardiaca"]),
    ("Orthosiphonis folium", "traditional", ["Orthosiphon aristatus", "Orthosiphon stamineus"]),
    ("Echinaceae angustifoliae radix", "traditional", ["Echinacea angustifolia"]),
    ("Echinaceae pallidae radix", "traditional", ["Echinacea pallida"]),
    ("Echinaceae purpureae herba", "both", ["Echinacea purpurea"]),
    ("Taraxaci folium", "traditional", ["Taraxacum officinale"]),
    ("Matricariae flos", "traditional", ["Matricaria recutita"]),
    ("Millefolii herba", "traditional", ["Achillea millefolium"]),
    ("Calendulae flos", "traditional", ["Calendula officinalis"]),
    ("Absinthii herba", "traditional", ["Artemisia absinthium"]),
    ("Centaurii herba", "traditional", ["Centaurium erythraea"]),
    ("Arctii radix", "traditional", ["Arctium lappa"]),
    ("Cynarae folium", "traditional", ["Cynara scolymus", "Cynara cardunculus"]),
    ("Silybi mariani fructus", "traditional", ["Silybum marianum"]),
    ("Solidaginis virgaureae herba", "traditional", ["Solidago virgaurea"]),
    ("Helichrysi flos", "traditional", ["Helichrysum arenarium"]),
    ("Tanaceti parthenii herba", "traditional", ["Tanacetum parthenium"]),
    ("Chamomillae romanae flos", "traditional", ["Chamaemelum nobile"]),
    ("Cichorii intybi radix", "traditional", ["Cichorium intybus"]),
    ("Pilosellae herba cum radice", "traditional", ["Pilosella officinarum"]),
]

if __name__ == "__main__":
    out = []
    for sub, use, names in ROWS:
        url = "https://www.ema.europa.eu/en/medicines/herbal/" + sub.lower().replace(" ", "-")
        time.sleep(1.2)
        r = requests.get(url, headers=UA, timeout=40)
        txt = re.sub(r"\s+", " ", html.unescape(re.sub(r"<script.*?</script>|<style.*?</style>|<[^>]+>", " ", r.text, flags=re.S))) if r.ok else ""
        for n in names:
            if re.search(re.escape(n).replace("×", "[×x]").replace(r"\ ", r"\s*"), txt):
                out.append(dict(taxon=n, ema_substance=sub, use=use, source=f"{OVERVIEW}; {url}"))
            else:
                print("NOT VERIFIED, skipped:", n, "on", url, file=sys.stderr)
    p = Path(__file__).resolve().parents[1] / "data" / "ema_monographs.csv"
    pd.DataFrame(out).to_csv(p, index=False)
    print(len(out), "taxa written to", p)
