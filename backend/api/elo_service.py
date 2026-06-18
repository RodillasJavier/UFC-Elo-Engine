"""
backend/api/elo_service.py

Elo computation service for the UFC Elo API.

Loads ufcfights.csv once, runs a full chronological Elo simulation, and caches
the results in module-level state so every API request reads from memory.

Data file is resolved from the UFC_DATA_FILE env var (falls back to
data/raw/ufcfights.csv relative to the repo root).
"""

import os
import pandas as pd
from typing import Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
DATA_FILE = os.environ.get(
    "UFC_DATA_FILE",
    os.path.join(ROOT_DIR, "data/raw/ufcfights.csv"),
)

_data: Optional[dict] = None

WC_ORDER = [
    "Women's Strawweight", "Women's Flyweight", "Women's Bantamweight",
    "Women's Featherweight", "Strawweight", "Flyweight", "Bantamweight",
    "Featherweight", "Lightweight", "Welterweight", "Middleweight",
    "Light Heavyweight", "Heavyweight", "Super Heavyweight",
    "Catch Weight", "Open Weight",
]


def _clean_method(m: str) -> str:
    """Collapse raw method strings to KO, SUB, or the original value (stripped)."""
    m = str(m)
    if "KO" in m:
        return "KO"
    if "SUB" in m:
        return "SUB"
    return m.strip()


def _clean_result(r: str) -> str:
    """Normalise result strings to 'win', 'draw', or 'nc'."""
    r = str(r)
    if "nc" in r:
        return "nc"
    if "draw" in r:
        return "draw"
    return r.strip()


def _get_k_factor(method: str, base_k: float = 40.0) -> float:
    """Return K=46 for KO/SUB finishes, K=40 for decisions."""
    return base_k * 1.15 if method in ("KO", "SUB") else base_k


def _expected_score(a: float, b: float) -> float:
    """Standard Elo expected score for fighter a against fighter b."""
    return 1 / (1 + 10 ** ((b - a) / 400))


def _update_elo(w: float, l: float, k: float, result: str = "win"):
    """Apply one Elo update; returns (new_w_elo, new_l_elo). No change for 'nc'."""
    exp = _expected_score(w, l)
    if result == "win":
        return round(w + k * (1 - exp), 2), round(l + k * (0 - (1 - exp)), 2)
    elif result == "draw":
        return round(w + k * (0.5 - exp), 2), round(l + k * (0.5 - (1 - exp)), 2)
    return w, l


def _load_and_compute() -> dict:
    """
    Load the fight CSV, run the full Elo simulation in chronological order, and
    return a dict with: elo_ratings, peak_elo_ratings, fighter_primary_wc,
    fighter_records, fighter_ranks, fights_df, and weight_classes.
    """
    df = pd.read_csv(DATA_FILE)
    df["method"] = df["method"].apply(_clean_method)
    df["result"] = df["result"].apply(_clean_result)

    df = df.iloc[::-1].reset_index(drop=True)

    elo_ratings: dict[str, float] = {}
    peak_elo_ratings: dict[str, float] = {}
    fighter_weight_classes: dict[str, dict[str, int]] = {}
    fighter_records: dict[str, dict[str, int]] = {}

    initial_elo = 1000.0

    df["f1_elo_start"] = 0.0
    df["f2_elo_start"] = 0.0
    df["f1_elo_end"] = 0.0
    df["f2_elo_end"] = 0.0

    for idx, row in df.iterrows():
        f1, f2 = row["fighter_1"], row["fighter_2"]

        for f in (f1, f2):
            if f not in elo_ratings:
                elo_ratings[f] = initial_elo
                peak_elo_ratings[f] = initial_elo
            if f not in fighter_records:
                fighter_records[f] = {"wins": 0, "losses": 0, "draws": 0}

        e1, e2 = elo_ratings[f1], elo_ratings[f2]
        k = _get_k_factor(row["method"])

        df.at[idx, "f1_elo_start"] = e1
        df.at[idx, "f2_elo_start"] = e2

        result = row["result"]
        if result == "win":
            n1, n2 = _update_elo(e1, e2, k, "win")
            fighter_records[f1]["wins"] += 1
            fighter_records[f2]["losses"] += 1
        elif result == "draw":
            n1, n2 = _update_elo(e1, e2, k, "draw")
            fighter_records[f1]["draws"] += 1
            fighter_records[f2]["draws"] += 1
        else:
            n1, n2 = e1, e2

        df.at[idx, "f1_elo_end"] = n1
        df.at[idx, "f2_elo_end"] = n2
        elo_ratings[f1] = n1
        elo_ratings[f2] = n2
        peak_elo_ratings[f1] = max(peak_elo_ratings[f1], n1)
        peak_elo_ratings[f2] = max(peak_elo_ratings[f2], n2)

        wc = str(row.get("weight", "")).strip() if "weight" in df.columns else ""
        if wc and wc != "nan":
            for f in (f1, f2):
                if f not in fighter_weight_classes:
                    fighter_weight_classes[f] = {}
                fighter_weight_classes[f][wc] = fighter_weight_classes[f].get(wc, 0) + 1

    fighter_primary_wc = {
        f: max(wc_counts, key=lambda k: wc_counts[k])
        for f, wc_counts in fighter_weight_classes.items()
    }

    all_wc = sorted(
        set(fighter_primary_wc.values()),
        key=lambda x: WC_ORDER.index(x) if x in WC_ORDER else 99,
    )

    fighter_ranks = {
        f: i + 1
        for i, (f, _) in enumerate(
            sorted(elo_ratings.items(), key=lambda x: x[1], reverse=True)
        )
    }

    return {
        "elo_ratings": elo_ratings,
        "peak_elo_ratings": peak_elo_ratings,
        "fighter_primary_wc": fighter_primary_wc,
        "fighter_records": fighter_records,
        "fighter_ranks": fighter_ranks,
        "fights_df": df,
        "weight_classes": all_wc,
    }


def get_fight_history(name: str) -> list[dict]:
    """Return a fighter's fights in reverse-chronological order from their perspective.

    Each entry contains: event, opponent, result, method, elo_before, elo_after, delta.
    Result is flipped to 'loss' when the fighter appeared as fighter_2 and lost.
    """
    data = get_data()
    df = data["fights_df"]
    mask = (df["fighter_1"] == name) | (df["fighter_2"] == name)

    history = []
    for _, row in df[mask].iterrows():
        if row["fighter_1"] == name:
            opponent, result = row["fighter_2"], row["result"]
            elo_before, elo_after = row["f1_elo_start"], row["f1_elo_end"]
        else:
            opponent = row["fighter_1"]
            result = "loss" if row["result"] == "win" else row["result"]
            elo_before, elo_after = row["f2_elo_start"], row["f2_elo_end"]

        elo_before, elo_after = round(float(elo_before), 1), round(float(elo_after), 1)
        history.append(
            {
                "event": row["event"],
                "opponent": opponent,
                "result": result,
                "method": row["method"],
                "elo_before": elo_before,
                "elo_after": elo_after,
                "delta": round(elo_after - elo_before, 1),
            }
        )

    history.reverse()
    return history


def get_data() -> dict:
    """Return the cached Elo dataset, computing it on first call."""
    global _data
    if _data is None:
        _data = _load_and_compute()
    return _data
