"""
FastAPI application exposing the UFC Elo dataset over HTTP.

Endpoints:
  GET /api/weight_classes          — ordered list of weight class names
  GET /api/rankings                — paginated fighter rankings (current or peak Elo)
  GET /api/fighters/search?q=      — name substring search, returns top 10 matches
  GET /api/fighters/{name}         — full profile: stats + fight history

Elo data is preloaded at startup via the lifespan context so the first request
is not penalised by the CSV parse and simulation cost.

CORS origin is configured via the FRONTEND_URL env var (default localhost:5173).
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from . import elo_service


def _fmt_record(rec: dict) -> str:
    """Format a wins/losses/draws dict as a 'W-L-D' string."""
    return f"{rec['wins']}-{rec['losses']}-{rec['draws']}"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Preload the Elo dataset on startup so the first request is instant."""
    elo_service.get_data()
    yield


app = FastAPI(title="UFC Elo API", lifespan=lifespan)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:5173", "https://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Get weight classes
@app.get("/api/weight_classes")
def weight_classes():
    """Return all weight classes present in the dataset, sorted by WC_ORDER."""
    return elo_service.get_data()["weight_classes"]


# Get fighter rankings
@app.get("/api/rankings")
def rankings(
    type: str = Query("current"),
    weight_class: str = Query("all"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=200),
):
    """Return a paginated list of fighters ranked by current or peak Elo.

    Supports optional weight_class filter. Each row includes rank, fighter name,
    Elo, primary weight class, and W-L-D record.
    """
    data = elo_service.get_data()
    elo = data["elo_ratings"] if type != "peak" else data["peak_elo_ratings"]
    primary_wc = data["fighter_primary_wc"]
    records = data["fighter_records"]

    sorted_fighters = sorted(elo.items(), key=lambda x: x[1], reverse=True)

    if weight_class != "all":
        sorted_fighters = [
            (f, e) for f, e in sorted_fighters if primary_wc.get(f) == weight_class
        ]

    total = len(sorted_fighters)
    start = (page - 1) * per_page
    page_fighters = sorted_fighters[start : start + per_page]

    result = []
    for i, (f, e) in enumerate(page_fighters):
        rec = records.get(f, {"wins": 0, "losses": 0, "draws": 0})
        result.append(
            {
                "rank": start + i + 1,
                "fighter": f,
                "elo": round(e, 1),
                "weight_class": primary_wc.get(f, "Unknown"),
                "record": _fmt_record(rec),
            }
        )

    return {"total": total, "page": page, "per_page": per_page, "rankings": result}


# Search for fighters
@app.get("/api/fighters/search")
def search_fighters(q: str = Query(..., min_length=1)):
    """Return up to 10 fighters whose names contain q (case-insensitive), sorted by Elo."""
    data = elo_service.get_data()
    q_lower = q.lower()
    matches = [
        (f, e)
        for f, e in data["elo_ratings"].items()
        if q_lower in f.lower()
    ]
    matches.sort(key=lambda x: x[1], reverse=True)
    primary_wc = data["fighter_primary_wc"]
    return [
        {"name": f, "elo": round(e, 1), "weight_class": primary_wc.get(f, "Unknown")}
        for f, e in matches[:10]
    ]


# Get a specific fighter's profile
@app.get("/api/fighters/{name:path}")
def fighter_profile(name: str):
    """Return a fighter's full profile: current/peak Elo, record, rank, and fight history.

    Uses {name:path} so names containing slashes are captured correctly.
    Raises 404 if the fighter is not in the dataset.
    """
    data = elo_service.get_data()
    elo_ratings = data["elo_ratings"]

    if name not in elo_ratings:
        raise HTTPException(status_code=404, detail=f"Fighter '{name}' not found")

    rec = data["fighter_records"].get(name, {"wins": 0, "losses": 0, "draws": 0})

    return {
        "name": name,
        "current_elo": round(elo_ratings[name], 1),
        "peak_elo": round(data["peak_elo_ratings"].get(name, elo_ratings[name]), 1),
        "weight_class": data["fighter_primary_wc"].get(name, "Unknown"),
        "record": _fmt_record(rec),
        "wins": rec["wins"],
        "losses": rec["losses"],
        "draws": rec["draws"],
        "rank": data["fighter_ranks"].get(name),
        "fight_history": elo_service.get_fight_history(name),
    }
