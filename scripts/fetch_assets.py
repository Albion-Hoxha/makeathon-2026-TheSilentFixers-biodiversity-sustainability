"""Download licensed photos from Wikimedia Commons for the dashboard + record credits.
Run once: python scripts/fetch_assets.py   -> app/assets/species/*.jpg, app/assets/hero.jpg, app/assets/credits.json
Only CC / public-domain files are kept; the credits are shown on the Data & Methods page."""
import json, re, sys, time
from pathlib import Path
from urllib.parse import unquote, urlparse
import requests

H = {"User-Agent": "vanishing-apothecary-hackathon/0.1 (open-source hackathon project)"}
OUT = Path(__file__).resolve().parents[1] / "app" / "assets"
SPECIES = {"Salvia officinalis": "Salvia_officinalis", "Gentiana lutea": "Gentiana_lutea", "Arnica montana": "Arnica_montana",
           "Origanum vulgare": "Origanum_vulgare", "Hypericum perforatum": "Hypericum_perforatum"}
HERO = "Šar_Mountains"


def get(url, **kw):
    for wait in (2, 10, 30, 60, 120):  # Wikimedia answers 429 when called quickly
        time.sleep(wait)
        r = requests.get(url, headers=H, timeout=60, **kw)
        if r.status_code != 429:
            return r
    r.raise_for_status()


def photo(page, width, dest):
    src = (get("https://en.wikipedia.org/api/rest_v1/page/summary/" + page).json().get("originalimage") or {}).get("source")
    if not src:
        print("no image for", page); return None
    parts = unquote(urlparse(src).path).split("/")
    name = parts[-2] if "thumb" in parts else parts[-1]
    q = get("https://commons.wikimedia.org/w/api.php", params={"action": "query", "titles": "File:" + name, "prop": "imageinfo",
            "iiprop": "url|extmetadata", "iiurlwidth": width, "format": "json"}).json()["query"]["pages"]
    ii = next(iter(q.values()))["imageinfo"][0]
    m = ii["extmetadata"]
    lic = m.get("LicenseShortName", {}).get("value", "")
    if not re.search(r"CC|Public domain|PD", lic, re.I):
        print("skip (licence):", name, lic); return None
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(get(ii["thumburl"]).content)
    clean = lambda s: re.sub(r"<[^>]+>", "", s).strip()
    return {"file": dest.name, "title": name, "author": clean(m.get("Artist", {}).get("value", "unknown")), "licence": lic, "page": ii["descriptionurl"]}


if __name__ == "__main__":
    cf = OUT / "credits.json"
    credits = json.loads(cf.read_text()) if cf.exists() else {}  # resumable: finished files are skipped
    jobs = [(sp, pg, 700, OUT / "species" / f"{sp}.jpg") for sp, pg in SPECIES.items()] + \
           [("hero", HERO, 1400, OUT / "hero.jpg")]
    for key, page, width, dest in jobs:
        if credits.get(key) and dest.exists():
            continue
        credits[key] = photo(page, width, dest)
        cf.write_text(json.dumps(credits, indent=1, ensure_ascii=False))
    print(json.dumps(credits, indent=1, ensure_ascii=False))
