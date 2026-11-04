"""EU herbal monograph (EMA/HMPC) evidence level for a species, from data/ema_monographs.csv (built by scripts/build_ema_table.py)."""
from pathlib import Path
import pandas as pd

PATH = Path(__file__).resolve().parents[2] / "data" / "ema_monographs.csv"
LABEL = {"traditional": "traditional use", "well-established": "well-established use", "both": "well-established + traditional use"}
NONE = "no EU monograph"


def norm(taxon: str) -> str:
    return " ".join(taxon.replace("×", " ").replace(" x ", " ").lower().split())  # "Mentha × piperita" == "Mentha piperita"


def load_ema(path=PATH) -> dict:
    if not Path(path).exists():
        return {}
    d = pd.read_csv(path)
    return {norm(t): u for t, u in zip(d.taxon, d.use)}


def ema_label(taxon: str, table: dict) -> str:
    return LABEL.get(table.get(norm(taxon)), NONE) if table else "n/a"
