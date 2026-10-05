import os
import pandas as pd

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADV_PATH = os.path.join(BASE, "data", "seasonal_advisory.csv")

_df = None

def _load():
    global _df
    if _df is None:
        _df = pd.read_csv(ADV_PATH)

def get_seasonal_advisory(region: str, season: str) -> dict:
    _load()
    row = _df[(_df["region"] == region) & (_df["season"] == season)]
    if row.empty:
        return {"advisory": "No advisory available for this region and season."}
    r = row.iloc[0]
    return {
        "region": r["region"],
        "season": r["season"],
        "temp_range": f"{r['typical_temp_min']}°C – {r['typical_temp_max']}°C",
        "humidity": f"{r['typical_humidity']}%",
        "rainfall": f"{r['typical_rainfall']} mm",
        "advisory": r["advisory"],
    }

def get_regions() -> list:
    _load()
    return sorted(_df["region"].unique().tolist())
